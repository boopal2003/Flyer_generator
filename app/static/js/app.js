// app/static/js/app.js — rows layout + PDF extraction

document.addEventListener("DOMContentLoaded", () => {
  // State
  let filesState = []; // { name, b64, role, url? }
  let currentTemplate = "square_post";
  let shapeChoice = "bottle";
  let sectorChoice = "Beverages";
  let platformChoice = "instagram";
  let poseChoice = "flat_lay";

  // DOM
  const $ = (id) => document.getElementById(id);
  const pdfInput   = $("pdf");
  const btnPdf     = $("btnPdf");
  const pdfStatus  = $("pdfStatus");
  const artInput   = $("art");
  const filesDiv   = $("files");
  const flyerImg   = $("flyer");
  const statusDiv  = $("status");
  const btnFlyer   = $("btnFlyer");
  const actions    = $("actions");
  const btnDownload= $("btnDownload");
  const btnReset   = $("btnReset");
  const styleTA    = $("style");

  // Template tiles
  document.querySelectorAll(".tile").forEach((tile) => {
    tile.addEventListener("click", () => {
      document.querySelectorAll(".tile").forEach(t => t.classList.remove("active"));
      tile.classList.add("active");
      currentTemplate = tile.dataset.template;
    });
  });

  // Card groups
  bindCardGroup("shapeCards",   (val) => (shapeChoice    = val));
  bindCardGroup("sectorCards",  (val) => (sectorChoice   = val));
  bindCardGroup("platformCards",(val) => (platformChoice = val));
  bindCardGroup("poseCards", (val) => (poseChoice = val));
  function bindCardGroup(containerId, onPick) {
    const c = document.getElementById(containerId);
    if (!c) return;
    c.querySelectorAll(".card").forEach((card) => {
      card.addEventListener("click", () => {
        c.querySelectorAll(".card").forEach((x) => x.classList.remove("active"));
        card.classList.add("active");
        onPick(card.dataset.value);
      });
    });
  }

  // Helpers
  const PANEL_OPTIONS = ["front","back","left","right","top","bottom","cap","generic"];
  function inferRoleFromFilename(filename) {
    const n = (filename || "").toLowerCase();
    if (/\bfront\b|(^|[_-])f($|[_-])|\bmain\b/.test(n)) return "front";
    if (/\bback\b|(^|[_-])b($|[_-])|\bingr|nutrition|directions/.test(n)) return "back";
    if (/\bleft\b|(^|[_-])l($|[_-])/.test(n)) return "left";
    if (/\bright\b|(^|[_-])r($|[_-])/.test(n)) return "right";
    if (/\btop\b|(^|[_-])t($|[_-])|cap/.test(n)) return "top";
    if (/\bbottom\b|btm|(_|-)bottom\b/.test(n)) return "bottom";
    if (/\bcap\b/.test(n)) return "cap";
    return "generic";
  }

  async function fileToBase64(file) {
    return await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onerror = () => reject(new Error("FileReader failed"));
      reader.onload = () => {
        const result = reader.result || "";
        const comma = result.indexOf(",");
        if (comma === -1) return reject(new Error("Bad data URL"));
        resolve(result.slice(comma + 1));
      };
      reader.readAsDataURL(file);
    });
  }

  async function post(path, body) {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  // ---- PDF extraction flow ----
  btnPdf?.addEventListener("click", async () => {
    const file = pdfInput?.files?.[0];
    if (!file) { alert("Pick a PDF first."); return; }
    if (file.type !== "application/pdf") { alert("Please choose a PDF file."); return; }

    pdfStatus.textContent = "Extracting panels from PDF…";
    btnPdf.disabled = true;

    try {
      const pdf_b64 = await fileToBase64(file);
      const out = await post("/api/pdf_extract", { pdf_b64, dpi: 400 });

      if (!out.panels?.length) {
        pdfStatus.textContent = "No panels detected. You can still upload images manually.";
        return;
      }

      // Add returned panels to filesState
      out.panels.forEach((p, i) => {
        filesState.push({
          name: `pdf_panel_${i + 1}.png`,
          b64: p.image_b64,
          role: p.role || "generic",
          url: `data:image/png;base64,${p.image_b64}`,
        });
      });

      renderFileList();
      pdfStatus.textContent = `Added ${out.panels.length} panel(s) from ${out.pages} page(s).`;
    } catch (err) {
      console.error(err);
      pdfStatus.textContent = "Failed to extract panels. See console.";
    } finally {
      btnPdf.disabled = false;
    }
  });

  // ---- Image upload (kept) ----
  artInput.addEventListener("change", async (e) => {
    const picked = Array.from(e.target.files || []);
    if (!picked.length) return;
    const MAX_BYTES = 100 * 1024 * 1024;

    for (const file of picked) {
      try {
        if (!file.type.startsWith("image/")) continue;
        if (file.size > MAX_BYTES) continue;
        const b64 = await fileToBase64(file);
        const url = URL.createObjectURL(file);
        const role = inferRoleFromFilename(file.name);
        filesState.push({ name: file.name, b64, role, url });
      } catch (err) {
        console.error(`Failed to read ${file.name}:`, err);
      }
    }
    if (!filesState.length) alert("No valid images were added.");
    renderFileList();
    artInput.value = "";
  });

  // Render panels with role editors
  function renderFileList() {
    filesDiv.innerHTML = "";
    if (filesState.length) {
      const toolbar = document.createElement("div");
      toolbar.className = "flex items-center justify-between mb-2";
      const count = document.createElement("div");
      count.className = "text-xs text-slate-600";
      count.textContent = `${filesState.length} file(s)`;
      const clear = document.createElement("button");
      clear.textContent = "Clear all";
      clear.className = "text-xs underline text-slate-500";
      clear.onclick = () => { filesState = []; filesDiv.innerHTML = ""; };
      toolbar.appendChild(count); toolbar.appendChild(clear);
      filesDiv.appendChild(toolbar);
    }
    const PANEL_OPTIONS = ["front","back","left","right","top","bottom","cap","generic"];
    filesState.forEach((f, idx) => {
      const row = document.createElement("div");
      row.className = "grid grid-cols-auto gap-3 items-center";
      const img = document.createElement("img");
      img.src = f.url || `data:image/png;base64,${f.b64}`;
      img.className = "thumb";
      const right = document.createElement("div");
      const name = document.createElement("div");
      name.className = "text-sm font-medium";
      name.textContent = f.name;
      const controls = document.createElement("div");
      controls.className = "flex items-center gap-2 mt-1";
      const label = document.createElement("span");
      label.className = "text-xs text-slate-500";
      label.textContent = "role:";
      const select = document.createElement("select");
      select.className = "border rounded-xl p-2";
      PANEL_OPTIONS.forEach((p) => {
        const opt = document.createElement("option");
        opt.value = p; opt.textContent = p; if (p === f.role) opt.selected = true;
        select.appendChild(opt);
      });
      select.onchange = (ev) => { filesState[idx].role = ev.target.value; };
      const remove = document.createElement("button");
      remove.textContent = "remove";
      remove.className = "text-xs underline text-slate-400";
      remove.onclick = () => { filesState.splice(idx, 1); renderFileList(); };
      controls.appendChild(label); controls.appendChild(select); controls.appendChild(remove);
      right.appendChild(name); right.appendChild(controls);
      row.appendChild(img); row.appendChild(right);
      filesDiv.appendChild(row);
    });
  }

  // Resize & download
  async function downloadResizedPNG(imgEl, w, h, filename = "flyer.png") {
    const canvas = document.createElement("canvas");
    canvas.width = w; canvas.height = h;
    const ctx = canvas.getContext("2d");
    const iw = imgEl.naturalWidth, ih = imgEl.naturalHeight;
    const scale = Math.min(w / iw, h / ih);
    const dw = Math.round(iw * scale), dh = Math.round(ih * scale);
    const dx = Math.round((w - dw) / 2), dy = Math.round((h - dh) / 2);
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(imgEl, dx, dy, dw, dh);
    canvas.toBlob((blob) => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      URL.revokeObjectURL(a.href);
    }, "image/png");
  }

  // Generate
  btnFlyer.addEventListener("click", async () => {
    if (!filesState.length) { alert("Upload a PDF or images first."); return; }
    actions.classList.add("hidden");
    statusDiv.textContent = "Generating flyer...";
    btnFlyer.disabled = true;

    const images_b64  = filesState.map((f) => f.b64);
    const panel_roles = filesState.map((f) => f.role);
    const style       = styleTA.value;

    try {
    const out = await post("/api/flyer", {
    images_b64, panel_roles,
    shape: shapeChoice,
    sector: sectorChoice,
    style,
    template: currentTemplate,
    platform: platformChoice,
    pose: poseChoice,   // NEW
    });

      flyerImg.src = "data:image/png;base64," + out.image_b64;
      statusDiv.textContent = "Flyer ready.";
      actions.classList.remove("hidden");

      const nameMap = {
        square_post: "square-post.png", landscape_post: "landscape-post.png",
        story: "story.png", carousel: "carousel-1.png", thumbnail: "thumbnail.png",
        youtube_banner: "youtube-banner.png", web_banner: "web-banner.png",
        quote: "quote.png", presentation: "presentation.png", document: "document.png",
        print: "print.png", infographic: "infographic.png",
      };
      const fname = nameMap[currentTemplate] || "flyer.png";
      btnDownload.onclick = () => downloadResizedPNG(flyerImg, out.target_w, out.target_h, fname);

      btnReset.onclick = () => {
        filesState = []; filesDiv.innerHTML = ""; flyerImg.src = "";
        statusDiv.textContent = "Cleared. Ready for the next flyer.";
        actions.classList.add("hidden"); styleTA.value = "";
        setActiveByData(document.querySelectorAll(".tile"), "square_post"); currentTemplate = "square_post";
        setActiveByData(document.querySelectorAll("#shapeCards .card"), "bottle"); shapeChoice = "bottle";
        setActiveByData(document.querySelectorAll("#sectorCards .card"), "Beverages"); sectorChoice = "Beverages";
        setActiveByData(document.querySelectorAll("#platformCards .card"), "instagram"); platformChoice = "instagram";
        setActiveByData(document.querySelectorAll("#poseCards .card"), "flat_lay"); poseChoice = "flat_lay";
        if (pdfInput) pdfInput.value = "";
        if (artInput) artInput.value = "";
        if (pdfStatus) pdfStatus.textContent = "";
      };
    } catch (err) {
      console.error(err);
      statusDiv.textContent = "Error generating flyer. See console.";
    } finally {
      btnFlyer.disabled = false;
    }
  });

  function setActiveByData(nodeList, value) {
    nodeList.forEach((el) => {
      if (el.dataset.template === value || el.dataset.value === value) el.classList.add("active");
      else el.classList.remove("active");
    });
  }
});

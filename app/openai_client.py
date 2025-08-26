# app/openai_client.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from openai import OpenAI

# Optional in local dev; no effect on Render unless you provide a .env file
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

# Path to the encrypted key file. Override with env OPENAI_ENC_PATH if you put it elsewhere.
ENC_FILE = Path(os.getenv("OPENAI_ENC_PATH", "openai.key.enc"))

# Simple module-level cache so we decrypt only once
_cached_client: Optional[OpenAI] = None
_cached_api_key: Optional[str] = None


def _decrypt_key_from_file(enc_path: Path, master_key: str) -> str:
    """Decrypts the OpenAI API key from an encrypted file using a Fernet master key."""
    token_enc = enc_path.read_text().strip().encode()
    fernet = Fernet(master_key.encode())
    try:
        return fernet.decrypt(token_enc).decode()
    except InvalidToken as e:
        raise RuntimeError(
            "Failed to decrypt OPENAI key: invalid MASTER_KEY or corrupted openai.key.enc."
        ) from e


def _resolve_api_key() -> str:
    """
    Resolution priority:
      1) If MASTER_KEY and openai.key.enc exist -> decrypt and use that key
      2) Else, use OPENAI_API_KEY env var
    """
    # Try encrypted path first
    master = os.getenv("MASTER_KEY", "").strip()
    if master and ENC_FILE.exists():
        return _decrypt_key_from_file(ENC_FILE, master)

    # Fallback to plain env (useful locally or for quick diagnostics on Render)
    plain = os.getenv("OPENAI_API_KEY", "").strip()
    if plain:
        return plain

    # Nothing configured
    raise RuntimeError(
        "No OpenAI key configured. Provide either:\n"
        "- MASTER_KEY (env) + openai.key.enc (file in repo root or set OPENAI_ENC_PATH), or\n"
        "- OPENAI_API_KEY (env) as a fallback."
    )


def get_client() -> OpenAI:
    """
    Returns a cached OpenAI client initialized with the decrypted (or env) API key.
    """
    global _cached_client, _cached_api_key
    if _cached_client is not None:
        return _cached_client

    api_key = _resolve_api_key()
    _cached_api_key = api_key
    _cached_client = OpenAI(api_key=api_key)
    return _cached_client


# Optional helper: expose the resolved key for a one-time sanity check (do NOT log this in production).
def _get_api_key_for_debug() -> Optional[str]:
    return _cached_api_key

from flask import Flask
from .config import load_config
from .routes.flyer import bp as flyer_bp
from .routes.pdf_extract import bp as pdf_bp  # NEW

def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    load_config(app)

    app.register_blueprint(flyer_bp, url_prefix="/api")
    app.register_blueprint(pdf_bp,   url_prefix="/api")  # register

    @app.get("/")
    def index():
        from flask import render_template
        return render_template("index.html")

    return app

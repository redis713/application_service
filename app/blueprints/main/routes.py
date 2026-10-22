from flask import render_template
from app.blueprints.main import main_bp

@main_bp.route("/")
def index():
    return render_template("main/index.html")

@main_bp.route("/distant")
def distant():
    return render_template("main/distant.html")

@main_bp.route("/ochno")
def ochno():
    return render_template("main/ochka.html")

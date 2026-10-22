from flask import Blueprint

apply_bp = Blueprint("apply", __name__, url_prefix="/apply")

from app.blueprints.apply import routes

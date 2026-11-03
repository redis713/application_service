from flask import Blueprint

internal_bp = Blueprint("internal", __name__, url_prefix="/applications")

from app.blueprints.internal import routes

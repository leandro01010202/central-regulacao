from flask import Blueprint

scheduling_bp = Blueprint("scheduling", __name__, template_folder="../../templates/scheduling")

from . import routes  # noqa
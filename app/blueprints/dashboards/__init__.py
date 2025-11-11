from flask import Blueprint

dashboards_bp = Blueprint("dashboards", __name__, template_folder="../../templates/dashboards")

from . import routes  # noqa
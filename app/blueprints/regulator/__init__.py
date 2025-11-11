from flask import Blueprint

regulator_bp = Blueprint("regulator", __name__, template_folder="../../templates/regulator")

from . import routes  # noqa
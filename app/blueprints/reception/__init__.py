from flask import Blueprint

reception_bp = Blueprint("reception", __name__, template_folder="../../templates/reception")

from . import routes  # noqa
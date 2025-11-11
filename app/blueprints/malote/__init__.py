from flask import Blueprint

malote_bp = Blueprint("malote", __name__, template_folder="../../templates/malote")

from . import routes  # noqa
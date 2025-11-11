from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Importa as rotas para registrar os endpoints do blueprint.
# Este import precisa permanecer no final do arquivo.
from . import routes  # noqa: E402,F401
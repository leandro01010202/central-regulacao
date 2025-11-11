from flask_login import LoginManager

from .database import MySQLConnector
from .models.usuario import Usuario

mysql = MySQLConnector()
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id: str):
    from app.repositories import usuarios as usuarios_repo

    data = usuarios_repo.obter_por_id(int(user_id))
    if data:
        return Usuario.from_row(data)
    return None
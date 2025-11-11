import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "definir_chave_segura")
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    SESSION_COOKIE_SECURE = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=6)

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3307"))
    MYSQL_USER = os.getenv("MYSQL_USER", "")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "")
    MYSQL_POOL_NAME = "central_reg_pool"
    MYSQL_POOL_SIZE = int(os.getenv("MYSQL_POOL_SIZE", "8"))
    MYSQL_POOL_RESET_SESSION = True
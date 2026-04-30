import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "cambia_esto_por_una_clave_segura")

    # ── MySQL ──
    MYSQL_HOST     = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT     = int(os.environ.get("MYSQL_PORT", 3306))
    MYSQL_USER     = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "tu_password")
    MYSQL_DB       = os.environ.get("MYSQL_DB", "claro_agendamiento")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Redis / Celery ──
    REDIS_URL        = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER    = REDIS_URL
    CELERY_BACKEND   = REDIS_URL

    # ── Archivos ──
    UPLOAD_FOLDER  = os.path.join(os.path.dirname(__file__), "uploads")
    OUTPUT_FOLDER  = os.path.join(os.path.dirname(__file__), "outputs")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024   # 10 MB

    # ── Módulo Claro ──
    URL_BASE    = "https://moduloagenda.cable.net.co/index.php"
    URL_AGENDAR = "https://moduloagenda.cable.net.co/MGW/MGW/Agendamiento/index.php"
    ESPERA_NORMAL = 15
    ESPERA_MODAL  = 25

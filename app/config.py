import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# 1. Загрузка переменных из .env файла (если он создан в корне проекта)
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))
    except Exception:
        pass

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-placeholder")
    
    # База данных MySQL: берется из DATABASE_URL (systemd или .env), либо дефолтная заглушка
    _db_url = os.environ.get(
        "DATABASE_URL", 
        "mysql+pymysql://user:password@localhost/dbname?charset=utf8mb4"
    )
    if _db_url and _db_url.startswith("mysql://"):
        _db_url = _db_url.replace("mysql://", "mysql+pymysql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    }

    # Загрузка файлов
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    SCANS_FOLDER = os.path.join(UPLOAD_FOLDER, "scans")
    DOCX_TEMPLATES_FOLDER = os.path.join(BASE_DIR, "docx_templates")
    MAX_CONTENT_LENGTH = 30 * 1024 * 1024  # 30 МБ для качественных PDF/сканов
    ALLOWED_SCAN_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "tif", "tiff"}

    # Настройки приложения
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 10800  # 3 часа (в секундах) для комфортного заполнения больших заявок


# 2. Если в корне проекта создан пользовательский файл config.py,
# подтягиваем параметры (например, SQLALCHEMY_DATABASE_URI) оттуда
root_cfg_path = os.path.join(BASE_DIR, "config.py")
if os.path.exists(root_cfg_path):
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("root_user_config", root_cfg_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "Config"):
            for attr in dir(mod.Config):
                if not attr.startswith("__"):
                    setattr(Config, attr, getattr(mod.Config, attr))
    except Exception:
        pass

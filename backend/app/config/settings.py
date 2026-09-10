import os
from dotenv import load_dotenv

load_dotenv()


def _secret(name, default=""):
    file_path = os.getenv(f"{name}_FILE")
    if file_path:
        with open(file_path, encoding="utf-8") as handle:
            return handle.read().strip()
    return os.getenv(name, default)


class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001").rstrip("/")
    AI_BATCH_TIMEOUT_SECONDS = max(60.0, float(os.getenv("AI_BATCH_TIMEOUT_SECONDS", "600")))
    AUTO_APPROVE_EXACT_MATCHES = os.getenv(
        "AUTO_APPROVE_EXACT_MATCHES", "false"
    ).strip().lower() in {"true", "1", "yes", "on"}
    AUTO_APPROVE_MIN_SCORE = min(
        1.0, max(0.0, float(os.getenv("AUTO_APPROVE_MIN_SCORE", "0.95")))
    )
    MOCK_SAP_URL = os.getenv("MOCK_SAP_URL", "http://localhost:8002").rstrip("/")
    SAP_ODATA_URL = os.getenv("SAP_ODATA_URL", "").rstrip("/")
    SAP_ODATA_TOKEN = _secret("SAP_ODATA_TOKEN")
    SAP_OAUTH_TOKEN_URL = os.getenv("SAP_OAUTH_TOKEN_URL", "")
    SAP_OAUTH_CLIENT_ID = os.getenv("SAP_OAUTH_CLIENT_ID", "")
    SAP_OAUTH_CLIENT_SECRET = _secret("SAP_OAUTH_CLIENT_SECRET")
    SAP_CLIENT_CERT = os.getenv("SAP_CLIENT_CERT", "")
    SAP_CLIENT_KEY = os.getenv("SAP_CLIENT_KEY", "")
    SAP_RATE_LIMIT_PER_SECOND = float(os.getenv("SAP_RATE_LIMIT_PER_SECOND", "5"))
    SAP_VERIFY_TLS = os.getenv("SAP_VERIFY_TLS", "true").strip().lower() not in {
        "false", "0", "no", "off",
    }
    SAP_TIMEOUT_SECONDS = float(os.getenv("SAP_TIMEOUT_SECONDS", "30"))
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    IMPORT_QUEUE_MODE = os.getenv("IMPORT_QUEUE_MODE", "background").lower()
    MAX_IMPORT_FILE_BYTES = int(os.getenv("MAX_IMPORT_FILE_BYTES", str(25 * 1024 * 1024)))
    MAX_IMPORT_ROWS = int(os.getenv("MAX_IMPORT_ROWS", "100000"))
    IMPORT_CHUNK_SIZE = int(os.getenv("IMPORT_CHUNK_SIZE", "1000"))
    IMPORT_CLASSIFICATION_WORKERS = int(os.getenv("IMPORT_CLASSIFICATION_WORKERS", "4"))
    IMPORT_MAX_RETRIES = int(os.getenv("IMPORT_MAX_RETRIES", "3"))


settings = Settings()

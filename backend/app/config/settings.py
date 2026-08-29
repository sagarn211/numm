import os

from dotenv import load_dotenv


load_dotenv()


class Settings:

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        ""
    )

    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "development-secret-key"
    )

    ALGORITHM: str = os.getenv(
        "ALGORITHM",
        "HS256"
    )

    AI_SERVICE_URL: str = os.getenv(
        "AI_SERVICE_URL",
        "http://localhost:8001"
    )

    MOCK_SAP_URL: str = os.getenv(
        "MOCK_SAP_URL",
        "http://localhost:8002"
    )

    FRONTEND_URL: str = os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173"
    )


settings = Settings()
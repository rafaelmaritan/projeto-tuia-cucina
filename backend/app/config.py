from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+psycopg://tuia:tuia123@db:5432/tuia_db"
    SQLALCHEMY_ECHO: bool = False

    # API
    API_TITLE: str = "Tuia Cucina API"
    API_VERSION: str = "0.1.0"
    CORS_ORIGINS: str = "http://localhost:4173,http://127.0.0.1:4173"

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # development ou production

    # Security
    # IMPORTANTE: Deve ser lido do arquivo .env em produção
    # Se não estiver definida, use valor padrão (apenas desenvolvimento)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    INITIAL_ADMIN_EMAIL: str = ""
    INITIAL_ADMIN_NAME: str = ""
    INITIAL_ADMIN_PASSWORD: str = ""

    # Server
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()

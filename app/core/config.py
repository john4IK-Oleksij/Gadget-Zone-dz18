from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = ""
    mysql_url: str = ""
    mysql_private_url: str = ""
    mysql_public_url: str = ""
    mysqlhost: str = ""
    mysqlport: str = "3306"
    mysqluser: str = ""
    mysqlpassword: str = ""
    mysqldatabase: str = ""
    owner_email: str = "admin@gadgetzone.com"

    jwt_secret_key: SecretStr = SecretStr(
        "insecure-dev-secret-key-change-in-production-min32chars"
    )
    environment: Literal["development", "production", "test"] = "development"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7

    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_window_seconds: int = 60
    login_rate_limit: int = 10
    register_rate_limit: int = 5
    refresh_rate_limit: int = 30

    # Frontend origins allowed to call the API (VS Code Live Server by default).
    cors_origins: list[str] = [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ]

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        key = self.jwt_secret_key.get_secret_value().strip()
        
        # Якщо запущено у продакшені:
        if self.environment == "production":
            # Автоматично вмикаємо захищені HTTPS-куки 
            self.cookie_secure = True
            # 1. Забороняємо пустий або дефолтний ключ
            if not key or "insecure-dev" in key:
                raise ValueError(
                    "CRITICAL SECURITY: In production, JWT_SECRET_KEY must be "
                    "explicitly provided via environment variables and cannot be empty or default!"
                )
            # 2. Перевіряємо довжину ключа (мінімум 32 символи)
            if len(key) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters long in production!")
                
        return self

    @model_validator(mode="after")
    def resolve_database_url(self) -> "Settings":
        url = (self.database_url or "").strip()

        # If DATABASE_URL is empty or an unresolved Railway template literal like ${{MySQL...}}
        if not url or url.startswith("${{"):
            url = (
                self.mysql_url
                or self.mysql_private_url
                or self.mysql_public_url
                or ""
            ).strip()

        # Fallback to individual components if URL is still empty or unresolved
        if (not url or url.startswith("${{")) and self.mysqlhost and self.mysqluser:
            pwd = f":{self.mysqlpassword}" if self.mysqlpassword else ""
            db = f"/{self.mysqldatabase}" if self.mysqldatabase else ""
            url = f"mysql+aiomysql://{self.mysqluser}{pwd}@{self.mysqlhost}:{self.mysqlport}{db}"

        # Ensure correct async driver prefix
        if url.startswith("mysql://"):
            url = url.replace("mysql://", "mysql+aiomysql://", 1)
        elif url.startswith("mysql+pymysql://"):
            url = url.replace("mysql+pymysql://", "mysql+aiomysql://", 1)

        self.database_url = url
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

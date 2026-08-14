import os
from typing import Optional
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVICE_NAME: str = "user-service"
    PORT: int = 8001
    
    # Allow overriding database url directly (common in containerized setups)
    DATABASE_URL: Optional[str] = None
    
    # Or fall back to individual connection parameters
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "root@123"
    MYSQL_USERS_DB: str = "smartfarm_users"
    
    @property
    def db_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # quote_plus handles special characters in the password (e.g. root@123)
        return f"mysql+pymysql://{self.MYSQL_USER}:{quote_plus(self.MYSQL_PASSWORD)}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_USERS_DB}"

    class Config:
        env_file = "../.env"  # Look in parent directory for local running
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVICE_NAME: str = "monitoring-service"
    PORT: int = 8003
    
    # URL to verify farm_id existence
    FARM_SERVICE_URL: str = "http://localhost:8002"
    
    # MongoDB settings
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_USER: Optional[str] = None
    MONGODB_PASSWORD: Optional[str] = None
    MONGODB_DATABASE: str = "smartfarm_monitoring"
    
    # Can also define a full connection URL directly
    MONGODB_URL: Optional[str] = None
    
    @property
    def mongo_url(self) -> str:
        if self.MONGODB_URL:
            return self.MONGODB_URL
            
        # Build connection URL
        credentials = ""
        if self.MONGODB_USER and self.MONGODB_PASSWORD:
            credentials = f"{self.MONGODB_USER}:{self.MONGODB_PASSWORD}@"
            
        return f"mongodb://{credentials}{self.MONGODB_HOST}:{self.MONGODB_PORT}"

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

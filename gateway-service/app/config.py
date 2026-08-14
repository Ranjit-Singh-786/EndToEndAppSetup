from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "gateway-service"
    port: int = 3000
    user_service_url: str = "http://localhost:8001"
    farm_service_url: str = "http://localhost:8002"
    monitoring_service_url: str = "http://localhost:8003"

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

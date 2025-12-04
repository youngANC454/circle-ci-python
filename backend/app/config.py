from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    APP_NAME:  str= "CI?CD AI Optimizer"
    DEBUG: bool = True

    CIRCLECI_API_TOKEN: str = "" #write your circle api token here
    CIRCLECI_ORG_SLUG: str = "" #write your circle org slug here

    MONGODB_URL: str = "" #write your mongodb url here
    MONGODB_DB_NAME: str = "" #write your mongodb name here

    REDIS_HOST: str="redis"
    REDIS_PORT: int=6379
    # REDIS_PASSWORD: str=""

    ML_SERVICE_URL: str = "http://localhost:8001"

    CORS_ORIGINS:  str = "http://localhost:3000,http://localhost:8000,http://grafana:3000"
    

    PROMETHEUS_PORT: int = 9090

    LOG_LEVEL: str = "INFO"

    CIRCLECI_BASE_URL: str = "https://circleci.com/api/v2"
    MAX_BUILDS_PER_REQUEST: int = 100
    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    

settings = Settings()

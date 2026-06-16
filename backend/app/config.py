# backend/app/config.py

from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    DATABASE_URL:    str  = "postgresql://postgres:password@localhost:5432/churn_db"
    APP_NAME:        str  = "Churn Analytics API"
    APP_VERSION:     str  = "1.0.0"
    DEBUG:           bool = False
    ALLOWED_ORIGINS: List[str] = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://churn-analytics-wo2v-oue4lvob0-pmalipatil239-2834s-projects.vercel.app",
    "https://churn-analytics-wo2v.vercel.app",
    "https://*.vercel.app",
]
    MODEL_PATH:      str = "models_saved/"
    RANDOM_STATE:    int = 42

    class Config:
        env_file = ".env"
        extra    = "allow"

settings = Settings()
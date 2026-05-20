# backend/app/config.py

from pydantic_settings import BaseSettings
# WHY pydantic_settings: it reads from .env files AND validates types automatically.
# If DATABASE_URL is missing, your app crashes at startup with a clear error
# instead of mysteriously failing at runtime. Companies use this pattern universally.

class Settings(BaseSettings):
    # Database connection string
    # Format: postgresql://user:password@host:port/dbname
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/churndb"
    
    # App settings
    APP_NAME: str = "Churn Analytics API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # CORS - which frontend URLs are allowed to call this API
    # WHY: browsers block cross-origin requests by default for security.
    # We explicitly allow our React dev server (port 5173)
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # ML settings
    MODEL_PATH: str = "models_saved/"
    RANDOM_STATE: int = 42
    # WHY random_state=42: makes your model training reproducible.
    # Same data + same random_state = same model every time.
    # Critical for debugging: if results change, it's the data, not randomness.
    
    class Config:
        # Tells pydantic to read from .env file in the same directory
        env_file = ".env"
        # Allow extra fields (won't crash if .env has unknown vars)
        extra = "allow"

# Singleton pattern: create once, import everywhere
# WHY singleton: avoids re-reading the .env file on every import
settings = Settings()
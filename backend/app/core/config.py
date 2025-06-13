# backend/app/core/config.py

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from the backend directory
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    """
    Application settings.
    Values are loaded from environment variables.
    """
    APP_NAME: str = "Career Guidance Platform API"
    API_V1_STR: str = "/api/v1"
    
    # Ollama settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3") # Default model, can be overridden

    # Data paths
    # Construct absolute paths from the project root (backend directory)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent # This should point to backend/app/
    DATA_DIR: Path = BASE_DIR / "data"
    CAREER_DATA_PATH: Path = DATA_DIR / "career_data.json"
    PROCESSED_INTEREST_TAGS_PATH: Path = DATA_DIR / "processed_interest_tags.json"
    ROADMAPS_DATA_DIR: Path = DATA_DIR / "roadmaps_data"
    PREBUILT_JDS_PATH: Path = DATA_DIR / "prebuilt_jds.json"
    ML_DIR: Path = BASE_DIR / "ml"
    EMBEDDINGS_PKL_PATH: Path = ML_DIR / "embeddings.pkl"


    # CORS settings
    # Adjust origins as needed for your frontend URL
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(',')

    class Config:
        case_sensitive = True
        # env_file = ".env" # Handled by load_dotenv for flexibility

settings = Settings()

# Ensure data directories exist (optional, for robustness)
# settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
# settings.ROADMAPS_DATA_DIR.mkdir(parents=True, exist_ok=True)
# settings.ML_DIR.mkdir(parents=True, exist_ok=True)

# print(f"Data dir: {settings.DATA_DIR}")
# print(f"Career data path: {settings.CAREER_DATA_PATH}")
# print(f"Embeddings PKL path: {settings.EMBEDDINGS_PKL_PATH}")


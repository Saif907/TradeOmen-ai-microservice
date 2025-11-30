from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # ----------------------------------------------------------------------
    # Core Application & LLM Settings
    # ----------------------------------------------------------------------
    PORT: int = 8001
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # ----------------------------------------------------------------------
    # Main Backend Communication & Security
    # ----------------------------------------------------------------------
    MAIN_BACKEND_URL: str
    # Shared secret key that authenticates the main backend to this service
    AI_SERVICE_SECRET_KEY: str 
    
    # ----------------------------------------------------------------------
    # Pydantic Settings Configuration
    # ----------------------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True,
        # Set a prefix if you want to namespace all variables (optional)
        # env_prefix="AI_" 
    )

# Instantiate the settings object
settings = Settings()
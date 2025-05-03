import os
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Project details
    PROJECT_NAME: str = "Email Assistant"
    VERSION: str = "0.1.0"
    
    # Email settings
    EMAIL_HOST: str = os.getenv("EMAIL_HOST", "")
    EMAIL_USER: str = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    
    # API keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Telegram settings
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./email_assistant.db")
    
    # Application settings
    CHECK_INTERVAL: int = int(os.getenv("CHECK_INTERVAL", "300"))  # in seconds

settings = Settings() 
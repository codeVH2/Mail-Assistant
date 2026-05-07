from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file so it works regardless of working directory
_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg://privmail:privmail@localhost:5432/privmail"

    # AI provider: "local" uses Ollama, "cloud" uses Anthropic
    ai_provider: str = "local"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Anthropic (only needed when ai_provider=cloud)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"

    # Gmail OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/callback"

    # App
    secret_key: str = "change-me-in-production"
    debug: bool = True


settings = Settings()

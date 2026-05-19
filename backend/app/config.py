from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres@localhost:5433/youtube_transcripts"
    frontend_origin: str = "http://localhost:5174"
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4.1-mini"
    openrouter_site_url: str = "http://localhost:5174"
    openrouter_site_name: str = "YouTube Transcript Console"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

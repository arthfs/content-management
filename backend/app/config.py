from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    secret_key: str = "dev-insecure-change-me"
    database_url: str = "sqlite:///./app.db"
    frontend_origin: str = "http://localhost:3000"
    token_minutes: int = 60 * 24
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    tiktok_client_key: str = ""
    tiktok_client_secret: str = ""
    tiktok_redirect_uri: str = "http://localhost:3000/settings"

    @property
    def tiktok_configured(self) -> bool:
        return bool(self.tiktok_client_key and self.tiktok_client_secret)


settings = Settings()

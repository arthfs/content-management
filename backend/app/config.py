from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    secret_key: str = "dev-insecure-change-me"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/content_manager"
    test_database_url: str = ""
    # When false (default) login is bypassed and every request acts as the single local user.
    auth_required: bool = False
    default_user_email: str = "me@local"
    frontend_origin: str = "http://localhost:3000"
    token_minutes: int = 60 * 24
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    tiktok_client_key: str = ""
    tiktok_client_secret: str = ""
    tiktok_redirect_uri: str = "http://localhost:3000/settings"
    upload_dir: str = "uploads"
    max_upload_mb: int = 500

    @property
    def tiktok_configured(self) -> bool:
        return bool(self.tiktok_client_key and self.tiktok_client_secret)

    @property
    def sqlalchemy_database_url(self) -> URL:
        url = make_url(self.database_url)
        if url.drivername in {"postgres", "postgresql"}:
            url = url.set(drivername="postgresql+psycopg")
        if url.get_backend_name() != "postgresql":
            raise ValueError("DATABASE_URL must use PostgreSQL (Supabase is supported).")
        return url


settings = Settings()

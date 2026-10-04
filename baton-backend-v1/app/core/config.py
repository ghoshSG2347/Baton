from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    baton_env: str = "development"
    baton_access_key: str = ""
    github_token: str = ""
    frontend_origins: str = "http://localhost:5173,https://baton-85j60d9d0-hackathon2348sg-9289.vercel.app"
    max_file_size_bytes: int = 200_000
    max_total_context_bytes: int = 2_000_000
    max_files_per_analysis: int = 100
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False, extra="ignore")
    @property
    def cors_origins(self) -> list[str]:
        return [x.strip() for x in self.frontend_origins.split(",") if x.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()

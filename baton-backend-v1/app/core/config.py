from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr

class Settings(BaseSettings):
    baton_env: str = "development"
    baton_access_key: str = ""
    github_token: str = ""
    gemini_api_key: SecretStr = Field(default=SecretStr(''), exclude=True, repr=False)
    gemini_model: str = Field(default='', pattern=r'^[A-Za-z0-9._-]*$', max_length=100)
    ai_context_bytes: int = Field(default=120000, ge=16000, le=1000000)
    ai_input_bytes: int = Field(default=32000, ge=8000, le=120000)
    ai_timeout_seconds: int = Field(default=45, ge=5, le=120)
    ai_max_output_tokens: int = Field(default=2000, ge=256, le=8192)
    frontend_origins: str = "http://localhost:5173,https://baton-sigma-six.vercel.app"
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

"""Runtime secrets are used only for authentication/redaction, never evidence."""
from app.core.config import get_settings


def secret_values(*additional):
    settings = get_settings()
    return tuple(value for value in (*additional, settings.github_token,
                                    settings.baton_access_key,
                                    settings.gemini_api_key.get_secret_value())
                 if isinstance(value, str) and value)

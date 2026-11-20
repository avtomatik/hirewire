"""HeadHunter-specific settings. API functionality is dormant by default."""

from pathlib import Path
from urllib.parse import urlencode

from pydantic import BaseModel, Field, SecretStr


class OAuthSettings(BaseModel):
    client_id: str
    client_secret: SecretStr
    application_number: int | None = None  # Legacy SkillMapper metadata
    auth_url: str = "https://hh.ru/oauth/authorize"
    token_url: str = "https://api.hh.ru/token"
    redirect_scheme: str = "http"
    redirect_host: str = "localhost"
    redirect_port: int = 8080
    redirect_path: str = "/callback"
    authorization_timeout: float = 180.0

    @property
    def redirect_uri(self) -> str:
        return (
            f"{self.redirect_scheme}://{self.redirect_host}:"
            f"{self.redirect_port}{self.redirect_path}"
        )

    def authorization_url(self, state: str) -> str:
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "state": state,
            }
        )
        return f"{self.auth_url}{'&' if '?' in self.auth_url else '?'}{query}"


class HttpSettings(BaseModel):
    timeout: float = 15.0


class ApiSettings(BaseModel):
    base_url: str = "https://api.hh.ru"


class TokenStoreSettings(BaseModel):
    path: Path = Path(".state/hhru/tokens.json")


class HHRUSettings(BaseModel):
    """Provider configuration. No HeadHunter credentials needed by default."""

    api_enabled: bool = False
    oauth: OAuthSettings | None = None
    http: HttpSettings = Field(default_factory=HttpSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)
    token_store: TokenStoreSettings = Field(default_factory=TokenStoreSettings)

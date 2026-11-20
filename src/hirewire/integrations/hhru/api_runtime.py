"""Composition of the original SkillMapper API components; explicitly opt-in."""

from collections.abc import Iterator
from contextlib import contextmanager

from hirewire.config.paths import resolve_project_path
from hirewire.config.settings import Settings
from hirewire.integrations.hhru.api.client import APIClient
from hirewire.integrations.hhru.http.auth import BearerTokenAuth
from hirewire.integrations.hhru.http.client import HttpClient
from hirewire.integrations.hhru.oauth.browser import WebBrowserLauncher
from hirewire.integrations.hhru.oauth.clients import RequestsOAuthClient
from hirewire.integrations.hhru.oauth.flow import OAuthFlow
from hirewire.integrations.hhru.oauth.token_provider import OAuthTokenProvider
from hirewire.integrations.hhru.oauth.token_store import JsonTokenStore


def _configured(settings: Settings):
    if not settings.hhru.api_enabled:
        raise RuntimeError(
            "HeadHunter API is disabled. Enable HIREWIRE_HHRU__API_ENABLED "
            "only if your application has been granted access."
        )
    if settings.hhru.oauth is None:
        raise ValueError(
            "Configure HIREWIRE_HHRU__OAUTH__CLIENT_ID and CLIENT_SECRET."
        )
    return settings.hhru.oauth


def _provider(
    settings: Settings, oauth_client: RequestsOAuthClient
) -> OAuthTokenProvider:
    # No implicit migration or deletion of historical SkillMapper token files.
    token_path = resolve_project_path(settings.hhru.token_store.path)
    return OAuthTokenProvider(oauth_client, JsonTokenStore(token_path))


def authorize(settings: Settings) -> dict:
    oauth = _configured(settings)
    client = RequestsOAuthClient(oauth, timeout=settings.hhru.http.timeout)
    try:
        provider = _provider(settings, client)
        OAuthFlow(oauth, client, WebBrowserLauncher(), provider).authorize()
    finally:
        client.close()
    return {
        "authorized": True,
        "token_file": str(
            resolve_project_path(settings.hhru.token_store.path)
        ),
    }


@contextmanager
def api_client(settings: Settings) -> Iterator[APIClient]:
    oauth = _configured(settings)
    oauth_client = RequestsOAuthClient(
        oauth, timeout=settings.hhru.http.timeout
    )
    try:
        provider = _provider(settings, oauth_client)
        with HttpClient(
            settings.hhru.api.base_url,
            timeout=settings.hhru.http.timeout,
            auth=BearerTokenAuth(provider),
        ) as transport:
            yield APIClient(transport)
    finally:
        oauth_client.close()


def resumes(settings: Settings) -> list[dict]:
    with api_client(settings) as api:
        return [
            resume.model_dump(mode="json") for resume in api.get_my_resumes()
        ]


def recommendations(
    settings: Settings, resume_id: str | None = None
) -> list[dict]:
    """Return vacancies for one resume, or all of the account's resumes."""
    with api_client(settings) as api:
        ids = (
            [resume_id] if resume_id else [r.id for r in api.get_my_resumes()]
        )
        result = []
        for rid in ids:
            result.append(
                {
                    "resume_id": rid,
                    "vacancies": [
                        v.model_dump(mode="json")
                        for v in api.get_recommended_vacancies(rid)
                    ],
                }
            )
        return result

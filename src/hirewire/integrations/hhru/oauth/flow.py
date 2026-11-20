import secrets

from hirewire.integrations.hhru.oauth.callback import OAuthCallbackServer
from hirewire.integrations.hhru.oauth.protocols import (BrowserLauncher,
                                                        OAuthClient)
from hirewire.integrations.hhru.oauth.token_provider import OAuthTokenProvider
from hirewire.integrations.hhru.settings import OAuthSettings


class OAuthFlow:
    def __init__(
        self,
        settings: OAuthSettings,
        client: OAuthClient,
        browser: BrowserLauncher,
        provider: OAuthTokenProvider,
    ):
        self._settings = settings
        self._client = client
        self._browser = browser
        self._provider = provider

    def authorize(self) -> None:
        state = secrets.token_urlsafe(32)
        callback = OAuthCallbackServer(
            self._settings.redirect_host,
            self._settings.redirect_port,
            self._settings.redirect_path,
            state,
        )
        try:
            callback.start()
            self._browser.open(self._settings.authorization_url(state))
            code = callback.wait_for_code(self._settings.authorization_timeout)
            self._provider.install_tokens(
                self._client.exchange_code_for_token(code)
            )
        finally:
            callback.close()

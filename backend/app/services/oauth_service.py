"""OAuth flow helpers — state management, token exchange, user info."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field

import httpx

from app.services.oauth_registry import OAuthProvider


# ---------------------------------------------------------------------------
# State store — single-use, 10-minute TTL tokens
# ---------------------------------------------------------------------------

@dataclass
class _StateEntry:
    customer_id: str
    provider_id: str
    created_at: float


class OAuthStateStore:
    """In-memory store for CSRF state tokens."""

    _TTL = 600  # 10 minutes

    def __init__(self) -> None:
        self._store: dict[str, _StateEntry] = {}

    def create(self, customer_id: str, provider_id: str) -> str:
        self._purge_expired()
        token = secrets.token_urlsafe(32)
        self._store[token] = _StateEntry(
            customer_id=customer_id,
            provider_id=provider_id,
            created_at=time.time(),
        )
        return token

    def consume(self, token: str) -> _StateEntry | None:
        """Return and remove the entry, or None if missing/expired."""
        entry = self._store.pop(token, None)
        if entry is None:
            return None
        if time.time() - entry.created_at > self._TTL:
            return None
        return entry

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [k for k, v in self._store.items() if now - v.created_at > self._TTL]
        for k in expired:
            del self._store[k]


# Module-level singleton
state_store = OAuthStateStore()


# ---------------------------------------------------------------------------
# OAuth service
# ---------------------------------------------------------------------------

class OAuthService:

    async def get_authorization_url(
        self,
        provider: OAuthProvider,
        customer_id: str,
        callback_url: str,
    ) -> str:
        """Build the OAuth authorization URL and store a state token."""
        state = state_store.create(customer_id=customer_id, provider_id=provider.provider_id)

        import os
        client_id = os.getenv(provider.client_id_env, "")

        params: dict[str, str] = {
            "client_id": client_id,
            "redirect_uri": callback_url,
            "response_type": "code",
            "state": state,
        }
        if provider.scopes:
            params["scope"] = " ".join(provider.scopes)

        # Merge any extra auth params (e.g. access_type, prompt, audience)
        params.update(provider.extra_auth_params)

        qs = "&".join(f"{k}={httpx.URL('', params={k: v}).params[k]}" for k, v in params.items())
        # Use httpx to properly encode
        url = str(httpx.URL(provider.auth_url, params=params))
        return url

    async def exchange_code(
        self,
        provider: OAuthProvider,
        code: str,
        callback_url: str,
    ) -> dict:
        """Exchange authorization code for tokens."""
        import os
        client_id = os.getenv(provider.client_id_env, "")
        client_secret = os.getenv(provider.client_secret_env, "")

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": callback_url,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        headers: dict[str, str] = {"Accept": "application/json"}

        # Notion uses Basic Auth for token exchange
        auth = None
        if provider.provider_id == "notion":
            import base64
            credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"
            # Notion doesn't want client_id/secret in body
            del data["client_id"]
            del data["client_secret"]

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(provider.token_url, data=data, headers=headers, auth=auth)
            resp.raise_for_status()
            return resp.json()

    async def fetch_user_info(self, provider: OAuthProvider, access_token: str) -> dict:
        """GET the userinfo endpoint to retrieve account name/email."""
        if not provider.userinfo_url:
            return {}

        headers: dict[str, str] = {"Authorization": f"Bearer {access_token}"}

        # Notion requires version header
        if provider.provider_id == "notion":
            headers["Notion-Version"] = "2022-06-28"

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(provider.userinfo_url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def refresh_access_token(
        self,
        provider: OAuthProvider,
        refresh_token: str,
    ) -> dict:
        """Use a refresh token to get a new access token."""
        import os
        client_id = os.getenv(provider.client_id_env, "")
        client_secret = os.getenv(provider.client_secret_env, "")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(provider.token_url, data=data, headers={"Accept": "application/json"})
            resp.raise_for_status()
            return resp.json()

    async def check_connection_health(
        self,
        provider: OAuthProvider,
        access_token: str,
    ) -> tuple[bool, str]:
        """Test token validity by calling the userinfo endpoint.

        Returns (is_healthy, message).
        """
        if not provider.userinfo_url:
            return True, "No health check endpoint"

        try:
            await self.fetch_user_info(provider, access_token)
            return True, "Connected"
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                return False, "Token expired or revoked"
            return False, f"HTTP {exc.response.status_code}"
        except Exception as exc:
            return False, str(exc)


def extract_account_name(provider: OAuthProvider, userinfo: dict) -> str:
    """Extract a human-readable account identifier from userinfo response."""
    # Common patterns across providers
    for key in ("email", "mail", "userPrincipalName", "login", "username", "name", "display_name"):
        val = userinfo.get(key)
        if val and isinstance(val, str):
            return val

    # Nested patterns
    if "bot" in userinfo and isinstance(userinfo["bot"], dict):
        # Notion returns {bot: {owner: {user: {name, ...}}}}
        owner = userinfo["bot"].get("owner", {})
        user = owner.get("user", {})
        return user.get("name") or user.get("person", {}).get("email", "")

    return ""


# Module-level singleton
_oauth_service: OAuthService | None = None


def get_oauth_service() -> OAuthService:
    global _oauth_service
    if _oauth_service is None:
        _oauth_service = OAuthService()
    return _oauth_service

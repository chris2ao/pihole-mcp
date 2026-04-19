import time
from typing import Any

import httpx

from pihole_mcp.config import PiholeConfig
from pihole_mcp.errors import PiholeAPIError, PiholeAuthError


class PiholeClient:
    """Async HTTP client for Pi-hole v6 REST API with session auth and auto-refresh."""

    _REFRESH_BUFFER_SECONDS = 60

    def __init__(self, config: PiholeConfig):
        self._config = config
        self._http = httpx.AsyncClient(
            base_url=config.api_base,
            verify=config.verify_tls,
            timeout=config.timeout_seconds,
        )
        self._sid: str | None = None
        self._sid_expires_at: float = 0.0

    async def close(self) -> None:
        if self._sid:
            try:
                await self._http.delete(
                    "/auth",
                    headers={"X-FTL-SID": self._sid},
                )
            except Exception:
                pass
            self._sid = None
        await self._http.aclose()

    async def _authenticate(self) -> None:
        resp = await self._http.post(
            "/auth",
            json={"password": self._config.password},
        )
        if resp.status_code != 200:
            raise PiholeAuthError(
                f"Authentication failed: HTTP {resp.status_code} {resp.text}"
            )
        payload = resp.json()
        session = payload.get("session") or {}
        sid = session.get("sid")
        valid = session.get("valid") or session.get("validity")
        if not sid:
            raise PiholeAuthError(f"No session SID in auth response: {payload}")
        self._sid = sid
        validity_seconds = int(valid) if valid else 300
        self._sid_expires_at = time.time() + validity_seconds

    async def _ensure_session(self) -> str:
        now = time.time()
        if not self._sid or now >= (self._sid_expires_at - self._REFRESH_BUFFER_SECONDS):
            await self._authenticate()
        assert self._sid
        return self._sid

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> Any:
        """Issue a request, auto-authenticating and retrying once on 401."""
        sid = await self._ensure_session()
        resp = await self._http.request(
            method,
            path,
            params=params,
            json=json,
            headers={"X-FTL-SID": sid},
        )
        if resp.status_code == 401:
            self._sid = None
            sid = await self._ensure_session()
            resp = await self._http.request(
                method,
                path,
                params=params,
                json=json,
                headers={"X-FTL-SID": sid},
            )
        if resp.status_code >= 400:
            try:
                body = resp.json()
            except ValueError:
                body = resp.text
            raise PiholeAPIError(resp.status_code, f"{method} {path} failed", body)
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return await self.request("GET", path, params=params)

    async def post(self, path: str, *, json: Any | None = None) -> Any:
        return await self.request("POST", path, json=json)

    async def patch(self, path: str, *, json: Any | None = None) -> Any:
        return await self.request("PATCH", path, json=json)

    async def delete(self, path: str) -> Any:
        return await self.request("DELETE", path)

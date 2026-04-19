import httpx
import pytest
import respx

from pihole_mcp.client import PiholeClient
from pihole_mcp.config import PiholeConfig
from pihole_mcp.errors import PiholeAPIError, PiholeAuthError


@pytest.fixture
def cfg(monkeypatch):
    monkeypatch.setenv("PIHOLE_URL", "http://pihole.test")
    monkeypatch.setenv("PIHOLE_PASSWORD", "pw")
    return PiholeConfig()


@respx.mock
async def test_authenticate_success(cfg):
    respx.post("http://pihole.test/api/auth").mock(
        return_value=httpx.Response(
            200, json={"session": {"sid": "abc123", "valid": 300, "csrf": "c"}}
        )
    )
    respx.get("http://pihole.test/api/stats/summary").mock(
        return_value=httpx.Response(200, json={"total_queries": 42})
    )

    client = PiholeClient(cfg)
    result = await client.get("/stats/summary")
    assert result == {"total_queries": 42}
    await client.close()


@respx.mock
async def test_authenticate_failure(cfg):
    respx.post("http://pihole.test/api/auth").mock(
        return_value=httpx.Response(401, text="bad password")
    )

    client = PiholeClient(cfg)
    with pytest.raises(PiholeAuthError):
        await client.get("/stats/summary")
    await client.close()


@respx.mock
async def test_401_retry_reauths(cfg):
    auth_route = respx.post("http://pihole.test/api/auth").mock(
        return_value=httpx.Response(
            200, json={"session": {"sid": "sid1", "valid": 300}}
        )
    )
    stats_route = respx.get("http://pihole.test/api/stats/summary").mock(
        side_effect=[
            httpx.Response(401, json={"error": "expired"}),
            httpx.Response(200, json={"total_queries": 1}),
        ]
    )

    client = PiholeClient(cfg)
    result = await client.get("/stats/summary")
    assert result == {"total_queries": 1}
    assert auth_route.call_count == 2
    assert stats_route.call_count == 2
    await client.close()


@respx.mock
async def test_api_error_propagates(cfg):
    respx.post("http://pihole.test/api/auth").mock(
        return_value=httpx.Response(
            200, json={"session": {"sid": "x", "valid": 300}}
        )
    )
    respx.post("http://pihole.test/api/dns/blocking").mock(
        return_value=httpx.Response(400, json={"error": "bad request"})
    )

    client = PiholeClient(cfg)
    with pytest.raises(PiholeAPIError) as exc_info:
        await client.post("/dns/blocking", json={"blocking": True})
    assert exc_info.value.status_code == 400
    await client.close()


@respx.mock
async def test_session_cached_across_requests(cfg):
    auth_route = respx.post("http://pihole.test/api/auth").mock(
        return_value=httpx.Response(
            200, json={"session": {"sid": "cached", "valid": 3600}}
        )
    )
    respx.get("http://pihole.test/api/stats/summary").mock(
        return_value=httpx.Response(200, json={})
    )
    respx.get("http://pihole.test/api/dns/blocking").mock(
        return_value=httpx.Response(200, json={})
    )

    client = PiholeClient(cfg)
    await client.get("/stats/summary")
    await client.get("/dns/blocking")
    assert auth_route.call_count == 1
    await client.close()


@respx.mock
async def test_close_calls_delete_auth(cfg):
    respx.post("http://pihole.test/api/auth").mock(
        return_value=httpx.Response(200, json={"session": {"sid": "sid", "valid": 300}})
    )
    respx.get("http://pihole.test/api/stats/summary").mock(
        return_value=httpx.Response(200, json={})
    )
    logout_route = respx.delete("http://pihole.test/api/auth").mock(
        return_value=httpx.Response(204)
    )

    client = PiholeClient(cfg)
    await client.get("/stats/summary")
    await client.close()
    assert logout_route.call_count == 1

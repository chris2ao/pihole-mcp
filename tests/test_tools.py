import httpx
import pytest
import respx
from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient
from pihole_mcp.config import PiholeConfig
from pihole_mcp.tools import register_all


@pytest.fixture
def cfg(monkeypatch):
    monkeypatch.setenv("PIHOLE_URL", "http://pihole.test")
    monkeypatch.setenv("PIHOLE_PASSWORD", "pw")
    return PiholeConfig()


@respx.mock
async def test_register_all_counts_28(cfg):
    mcp = FastMCP("test")
    client = PiholeClient(cfg)
    count = register_all(mcp, client)
    assert count == 28
    await client.close()


@respx.mock
async def test_stats_summary_tool(cfg):
    respx.post("http://pihole.test/api/auth").mock(
        return_value=httpx.Response(200, json={"session": {"sid": "s", "valid": 300}})
    )
    respx.get("http://pihole.test/api/stats/summary").mock(
        return_value=httpx.Response(200, json={"total_queries": 100, "blocked_queries": 10})
    )

    client = PiholeClient(cfg)
    result = await client.get("/stats/summary")
    assert result["total_queries"] == 100
    await client.close()


@respx.mock
async def test_local_dns_add_a_record_builds_delta(cfg):
    respx.post("http://pihole.test/api/auth").mock(
        return_value=httpx.Response(200, json={"session": {"sid": "s", "valid": 300}})
    )
    respx.get("http://pihole.test/api/config/dns").mock(
        return_value=httpx.Response(
            200,
            json={"config": {"dns": {"hosts": ["192.168.1.1 router"], "cnameRecords": []}}},
        )
    )
    patch_route = respx.patch("http://pihole.test/api/config/dns").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )

    client = PiholeClient(cfg)
    from pihole_mcp.tools.local_dns import _current_dns_config, _patch_dns

    dns = await _current_dns_config(client)
    hosts = [h for h in dns["hosts"] if not h.endswith(" newhost")]
    hosts.append("10.0.0.5 newhost")
    await _patch_dns(client, {"hosts": hosts})

    assert patch_route.call_count == 1
    body = patch_route.calls[0].request.content
    assert b"10.0.0.5 newhost" in body
    assert b"192.168.1.1 router" in body
    await client.close()


@respx.mock
async def test_domains_remove_urlencodes_domain(cfg):
    respx.post("http://pihole.test/api/auth").mock(
        return_value=httpx.Response(200, json={"session": {"sid": "s", "valid": 300}})
    )
    route = respx.delete(
        "http://pihole.test/api/domains/allow/exact/ads.example.com"
    ).mock(return_value=httpx.Response(204))

    client = PiholeClient(cfg)
    await client.delete("/domains/allow/exact/ads.example.com")
    assert route.call_count == 1
    await client.close()

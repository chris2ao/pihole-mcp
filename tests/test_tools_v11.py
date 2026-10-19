import httpx
import pytest
import respx
from fastmcp import Client, FastMCP

from pihole_mcp.client import PiholeClient
from pihole_mcp.config import PiholeConfig
from pihole_mcp.tools import register_all
from pihole_mcp.tools.settings import redact

BASE = "http://pihole.test/api"


@pytest.fixture
async def mcp_client(monkeypatch):
    monkeypatch.setenv("PIHOLE_URL", "http://pihole.test")
    monkeypatch.setenv("PIHOLE_PASSWORD", "pw")
    with respx.mock(assert_all_called=False) as router:
        router.post(f"{BASE}/auth").mock(
            return_value=httpx.Response(200, json={"session": {"sid": "s", "valid": 300}})
        )
        router.delete(f"{BASE}/auth").mock(return_value=httpx.Response(204))
        mcp = FastMCP("test")
        pihole = PiholeClient(PiholeConfig())
        register_all(mcp, pihole)
        async with Client(mcp) as c:
            yield c, router
        await pihole.close()


async def call(c, tool_name, **args):
    return (await c.call_tool(tool_name, args)).structured_content


async def test_query_log_sends_client_ip_and_new_filters(mcp_client):
    c, router = mcp_client
    route = router.get(f"{BASE}/queries").mock(return_value=httpx.Response(200, json={"queries": []}))
    await call(c, "get_query_log", client_ip="10.0.0.5", status="GRAVITY", disk=True)
    params = route.calls[0].request.url.params
    assert params["client_ip"] == "10.0.0.5"
    assert "client" not in params
    assert params["status"] == "GRAVITY"
    assert params["disk"] == "true"


async def test_update_gravity_parses_text_output(mcp_client):
    c, router = mcp_client
    router.post(f"{BASE}/action/gravity").mock(
        return_value=httpx.Response(200, text="line1\nline2\n  [i] Done.", headers={"content-type": "text/plain"})
    )
    result = await call(c, "update_gravity", output_lines=2)
    assert result == {"status": "done", "output": ["line2", "  [i] Done."]}


async def test_update_gravity_reports_busy_on_409(mcp_client):
    c, router = mcp_client
    router.post(f"{BASE}/action/gravity").mock(return_value=httpx.Response(409, json={"error": {}}))
    result = await call(c, "update_gravity")
    assert result["status"] == "busy"


async def test_flush_cache_uses_restartdns(mcp_client):
    c, router = mcp_client
    route = router.post(f"{BASE}/action/restartdns").mock(return_value=httpx.Response(200, json={"status": "OK"}))
    await call(c, "flush_cache")
    assert route.call_count == 1


async def test_tail_log_trims_client_side(mcp_client):
    c, router = mcp_client
    route = router.get(f"{BASE}/logs/ftl").mock(
        return_value=httpx.Response(200, json={"log": [{"message": str(i)} for i in range(5)], "nextID": 5})
    )
    result = await call(c, "get_tail_log", log="ftl", lines=2, next_id=3)
    assert [e["message"] for e in result["log"]] == ["3", "4"]
    assert route.calls[0].request.url.params["nextID"] == "3"


async def test_stats_time_range_uses_database_endpoint(mcp_client):
    c, router = mcp_client
    route = router.get(f"{BASE}/stats/database/top_clients").mock(return_value=httpx.Response(200, json={"clients": []}))
    await call(c, "get_top_clients", count=5, from_ts=1, until_ts=2)
    params = route.calls[0].request.url.params
    assert (params["from"], params["until"], params["count"]) == ("1", "2", "5")


async def test_client_history_database_variant(mcp_client):
    c, router = mcp_client
    route = router.get(f"{BASE}/history/database/clients").mock(return_value=httpx.Response(200, json={}))
    await call(c, "get_client_history", from_ts=1, until_ts=2)
    assert route.call_count == 1


async def test_search_domain(mcp_client):
    c, router = mcp_client
    route = router.get(f"{BASE}/search/ads.example.com").mock(return_value=httpx.Response(200, json={"search": {}}))
    await call(c, "search_domain", domain="ads.example.com")
    assert route.calls[0].request.url.params["N"] == "20"


async def test_add_regex_domain(mcp_client):
    c, router = mcp_client
    route = router.post(f"{BASE}/domains/deny/regex").mock(return_value=httpx.Response(201, json={}))
    await call(c, "add_domain", domain=r"^ads\.", domain_type="deny", kind="regex")
    assert b'"domain":"^ads\\\\."' in route.calls[0].request.content.replace(b" ", b"")


async def test_remove_adlist_previews_without_confirm(mcp_client):
    c, router = mcp_client
    router.get(url__startswith=f"{BASE}/lists/").mock(return_value=httpx.Response(200, json={"lists": [{"id": 1}]}))
    delete = router.delete(url__startswith=f"{BASE}/lists/").mock(return_value=httpx.Response(204))
    result = await call(c, "remove_adlist", address="https://x.test/list.txt")
    assert result["preview"] is True
    assert delete.call_count == 0
    await call(c, "remove_adlist", address="https://x.test/list.txt", confirm=True)
    assert delete.call_count == 1


async def test_restart_dns_requires_confirm(mcp_client):
    c, router = mcp_client
    route = router.post(f"{BASE}/action/restartdns").mock(return_value=httpx.Response(200, json={}))
    assert (await call(c, "restart_dns"))["preview"] is True
    assert route.call_count == 0


async def test_update_config_patches_nested_body(mcp_client):
    c, router = mcp_client
    route = router.patch(f"{BASE}/config").mock(return_value=httpx.Response(200, json={"config": {}}))
    await call(c, "update_config", element="dns.upstreams", value=["9.9.9.9"], confirm=True)
    assert b'"upstreams":["9.9.9.9"]' in route.calls[0].request.content.replace(b" ", b"")


async def test_update_config_refuses_auth_settings(mcp_client):
    c, _ = mcp_client
    result = await c.call_tool("update_config", {"element": "webserver.api.pwhash", "value": "x"}, raise_on_error=False)
    assert result.is_error


async def test_get_config_redacts_secrets(mcp_client):
    c, router = mcp_client
    router.get(f"{BASE}/config/webserver").mock(
        return_value=httpx.Response(200, json={"config": {"webserver": {"api": {"pwhash": "abc", "totp_secret": ""}}}})
    )
    result = await call(c, "get_config", element="webserver")
    api = result["config"]["webserver"]["api"]
    assert api["pwhash"] == "<redacted>"
    assert api["totp_secret"] == ""


def test_redact_nested_lists():
    assert redact([{"app_pwhash": "h"}]) == [{"app_pwhash": "<redacted>"}]


async def test_export_teleporter_writes_zip(mcp_client, tmp_path):
    c, router = mcp_client
    router.get(f"{BASE}/teleporter").mock(
        return_value=httpx.Response(200, content=b"PK\x03\x04", headers={"content-type": "application/zip"})
    )
    result = await call(c, "export_teleporter", output_dir=str(tmp_path))
    assert result["bytes"] == 4
    assert (tmp_path / result["path"].split("/")[-1]).read_bytes() == b"PK\x03\x04"


async def test_export_teleporter_rejects_missing_dir(mcp_client, tmp_path):
    c, _ = mcp_client
    result = await c.call_tool("export_teleporter", {"output_dir": str(tmp_path / "nope")}, raise_on_error=False)
    assert result.is_error


async def test_network_and_info_read_tools(mcp_client):
    c, router = mcp_client
    dev = router.get(f"{BASE}/network/devices").mock(return_value=httpx.Response(200, json={"devices": []}))
    ver = router.get(f"{BASE}/info/version").mock(return_value=httpx.Response(200, json={"version": {}}))
    await call(c, "list_network_devices")
    await call(c, "get_version")
    assert dev.call_count == ver.call_count == 1


SMOKE = [
    ("get_blocking_status", {}, "GET", "/dns/blocking"),
    ("enable_blocking", {}, "POST", "/dns/blocking"),
    ("disable_blocking", {"duration_seconds": 30}, "POST", "/dns/blocking"),
    ("get_whitelist", {}, "GET", "/domains/allow/exact"),
    ("get_blacklist", {}, "GET", "/domains/deny/exact"),
    ("add_to_whitelist", {"domain": "a.test", "comment": "c"}, "POST", "/domains/allow/exact"),
    ("add_to_blacklist", {"domain": "a.test", "comment": "c"}, "POST", "/domains/deny/exact"),
    ("remove_from_whitelist", {"domain": "a.test"}, "DELETE", "/domains/allow/exact/a.test"),
    ("remove_from_blacklist", {"domain": "a.test"}, "DELETE", "/domains/deny/exact/a.test"),
    ("list_domains", {"domain_type": "allow", "kind": "regex"}, "GET", "/domains/allow/regex"),
    ("remove_domain", {"domain": "a.test", "domain_type": "deny"}, "DELETE", "/domains/deny/exact/a.test"),
    ("list_adlists", {"list_type": "block"}, "GET", "/lists"),
    ("add_adlist", {"address": "https://x.test/l.txt"}, "POST", "/lists"),
    ("list_groups", {}, "GET", "/groups"),
    ("add_group", {"name": "iot"}, "POST", "/groups"),
    ("remove_group", {"name": "iot", "confirm": True}, "DELETE", "/groups/iot"),
    ("list_clients", {}, "GET", "/clients"),
    ("get_client_suggestions", {"count": 5}, "GET", "/clients/_suggestions"),
    ("add_client", {"client_id": "10.0.0.5", "groups": [1]}, "POST", "/clients"),
    ("remove_client", {"client_id": "10.0.0.5"}, "DELETE", "/clients/10.0.0.5"),
    ("get_system_info", {}, "GET", "/info/system"),
    ("get_host_info", {}, "GET", "/info/host"),
    ("get_sensors", {}, "GET", "/info/sensors"),
    ("get_ftl_info", {}, "GET", "/info/ftl"),
    ("get_database_info", {}, "GET", "/info/database"),
    ("get_metrics", {}, "GET", "/info/metrics"),
    ("get_messages", {}, "GET", "/info/messages"),
    ("delete_message", {"message_id": 3}, "DELETE", "/info/messages/3"),
    ("get_padd", {"full": True}, "GET", "/padd"),
    ("delete_network_device", {"device_id": 4, "confirm": True}, "DELETE", "/network/devices/4"),
    ("get_gateway", {}, "GET", "/network/gateway"),
    ("get_routes", {}, "GET", "/network/routes"),
    ("get_interfaces", {"detailed": True}, "GET", "/network/interfaces"),
    ("list_dhcp_leases", {}, "GET", "/dhcp/leases"),
    ("remove_dhcp_lease", {"ip": "10.0.0.9", "confirm": True}, "DELETE", "/dhcp/leases/10.0.0.9"),
    ("flush_logs", {}, "POST", "/action/flush/logs"),
    ("flush_arp", {"confirm": True}, "POST", "/action/flush/arp"),
    ("flush_network", {"confirm": True}, "POST", "/action/flush/network"),
    ("restart_dns", {"confirm": True}, "POST", "/action/restartdns"),
    ("add_config_item", {"element": "dns.upstreams", "value": "1.1.1.1", "confirm": True}, "PUT", "/config/dns/upstreams/1.1.1.1"),
    ("remove_config_item", {"element": "dns.upstreams", "value": "1.1.1.1", "confirm": True}, "DELETE", "/config/dns/upstreams/1.1.1.1"),
    ("get_stats", {}, "GET", "/stats/summary"),
    ("get_top_blocked", {}, "GET", "/stats/top_domains"),
    ("get_top_permitted", {"from_ts": 1, "until_ts": 2}, "GET", "/stats/database/top_domains"),
    ("get_query_types", {}, "GET", "/stats/query_types"),
    ("get_forward_destinations", {}, "GET", "/stats/upstreams"),
    ("get_recent_blocked", {}, "GET", "/stats/recent_blocked"),
    ("get_history", {"from_ts": 1, "until_ts": 2}, "GET", "/history/database"),
    ("get_client_history", {}, "GET", "/history/clients"),
    ("get_query_suggestions", {}, "GET", "/queries/suggestions"),
]


@pytest.mark.parametrize("name,args,method,path", SMOKE, ids=[s[0] for s in SMOKE])
async def test_tool_smoke(mcp_client, name, args, method, path):
    c, router = mcp_client
    route = router.route(method=method, url=f"{BASE}{path}").mock(return_value=httpx.Response(204))
    result = await c.call_tool(name, args)
    assert not result.is_error
    assert route.call_count == 1


@pytest.mark.parametrize("name,args", [
    ("update_domain", {"domain": "a.test", "domain_type": "allow", "new_type": "deny"}),
    ("update_adlist", {"address": "https://x.test/l.txt", "enabled": False}),
    ("update_group", {"name": "iot", "new_name": "things"}),
    ("update_client", {"client_id": "10.0.0.5", "groups": [2]}),
])
async def test_update_tools_read_then_put(mcp_client, name, args):
    c, router = mcp_client
    router.get(url__startswith=BASE).mock(return_value=httpx.Response(200, json={}))
    put = router.put(url__startswith=BASE).mock(return_value=httpx.Response(200, json={}))
    assert not (await c.call_tool(name, args)).is_error
    assert put.call_count == 1


async def test_preview_paths_make_no_writes(mcp_client):
    c, router = mcp_client
    router.get(url__startswith=BASE).mock(return_value=httpx.Response(200, json={"config": {}}))
    writes = [
        router.route(method=m, url__startswith=BASE).mock(return_value=httpx.Response(204))
        for m in ("POST", "PUT", "PATCH", "DELETE")
    ]
    for name, args in [
        ("update_config", {"element": "dns.upstreams", "value": ["9.9.9.9"]}),
        ("add_config_item", {"element": "dns.upstreams", "value": "1.1.1.1"}),
        ("remove_config_item", {"element": "dns.upstreams", "value": "1.1.1.1"}),
        ("remove_group", {"name": "iot"}),
        ("delete_network_device", {"device_id": 1}),
        ("remove_dhcp_lease", {"ip": "10.0.0.9"}),
        ("flush_arp", {}),
        ("flush_network", {}),
    ]:
        assert (await call(c, name, **args))["preview"] is True
    assert all(w.call_count == 0 for w in writes)


async def test_stats_rejects_half_open_range(mcp_client):
    c, _ = mcp_client
    assert (await c.call_tool("get_stats", {"from_ts": 1}, raise_on_error=False)).is_error


async def test_add_adlist_rejects_bad_scheme(mcp_client):
    c, _ = mcp_client
    assert (await c.call_tool("add_adlist", {"address": "ftp://x"}, raise_on_error=False)).is_error

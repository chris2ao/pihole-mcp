# pihole-mcp

[![test](https://github.com/chris2ao/pihole-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/chris2ao/pihole-mcp/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-compatible-6E56CF.svg)](https://modelcontextprotocol.io/)
[![Pi-hole v6](https://img.shields.io/badge/Pi--hole-v6-96060C.svg)](https://docs.pi-hole.net/)

Unified Pi-hole v6 MCP server. Consolidates the useful tools from three upstream MCPs (`aplaceforallmystuff/mcp-pihole`, `sbarbett/pihole-mcp-server`, `cwdcwd/mcp-server-pihole`) into one Python server that matches the `chris2ao-unifi-mcp` stack (FastMCP + httpx + Pydantic v2).

## Tools (72)

Stats (9): `get_stats`, `get_top_blocked`, `get_top_permitted`, `get_top_clients`, `get_query_types`, `get_forward_destinations`, `get_recent_blocked`, `get_history`, `get_client_history`. Pass `from_ts` and `until_ts` to any of them (except `get_recent_blocked`) to query the long-term database for any time range.

Queries (2): `get_query_log` (filters: time range, domain, client IP or name, upstream, query type, status, reply, DNSSEC, paging, `disk` for the long-term database), `get_query_suggestions`

Search (1): `search_domain` explains why a domain is blocked or allowed (matching lists, regexes, adlists, groups)

Blocking (3): `get_blocking_status`, `enable_blocking`, `disable_blocking` (with optional timer)

Domain lists (10): `list_domains`, `add_domain`, `update_domain`, `remove_domain` (allow/deny, exact/regex, groups, comments), plus the legacy exact-match `get_whitelist`, `get_blacklist`, `add_to_whitelist`, `add_to_blacklist`, `remove_from_whitelist`, `remove_from_blacklist`

Adlists (4): `list_adlists`, `add_adlist`, `update_adlist`, `remove_adlist`

Groups and clients (9): `list_groups`, `add_group`, `update_group`, `remove_group`, `list_clients`, `get_client_suggestions`, `add_client`, `update_client`, `remove_client`

Local DNS (5): `list_local_dns`, `add_local_a_record`, `remove_local_a_record`, `add_local_cname_record`, `remove_local_cname_record`

System info (10): `get_version`, `get_system_info`, `get_host_info`, `get_sensors`, `get_ftl_info`, `get_database_info`, `get_metrics`, `get_messages`, `delete_message`, `get_padd`

Network and DHCP (7): `list_network_devices`, `delete_network_device`, `get_gateway`, `get_routes`, `get_interfaces`, `list_dhcp_leases`, `remove_dhcp_lease`

Settings (4): `get_config`, `update_config`, `add_config_item`, `remove_config_item`

Maintenance (8): `update_gravity`, `flush_cache`, `restart_dns`, `flush_logs`, `flush_arp`, `flush_network`, `get_tail_log`, `export_teleporter`

Plus `server_info`.

## Safety

- Disruptive or destructive tools return a **preview** and change nothing unless called with `confirm=true`: `update_config`, `add_config_item`, `remove_config_item`, `restart_dns`, `flush_arp`, `flush_network`, `remove_adlist`, `remove_group`, `delete_network_device`, `remove_dhcp_lease`.
- `get_config` redacts password hashes and the TOTP secret. The settings tools refuse any change under `webserver.api` (authentication settings).
- `export_teleporter` writes the backup zip to a directory you name and never overwrites a file. The archive includes the password hash, so store it securely. Teleporter import is deliberately not exposed.

## Auth

Pi-hole v6 uses session-based auth. This server handles it automatically:

1. `POST /api/auth` with `{"password": "<app-password>"}` returns a session SID.
2. All subsequent calls include `X-FTL-SID: <sid>`.
3. On 401 or near-expiry, the client re-authenticates and retries once.
4. On shutdown, `DELETE /api/auth` releases the session.

**App password** is created in the Pi-hole Web UI: Settings > Web Interface > "Application password" > Generate. This is separate from the main admin web password and is the correct credential for API clients. App passwords also bypass two-factor (TOTP) login, which this server does not implement.

## Install

```bash
cd /Users/chris2ao/GitProjects/chris2ao-pihole-mcp
uv sync
cp .env.example .env   # fill in PIHOLE_URL and PIHOLE_PASSWORD
uv run pytest
```

Or via the wrapper (production use with Claude Code):

```bash
~/.claude/scripts/pihole-wrapper.sh
```

## Register with Claude Code

In `~/.claude.json`, add to `mcpServers`:

```json
"pihole": {
  "command": "/Users/chris2ao/.claude/scripts/pihole-wrapper.sh",
  "args": []
}
```

The wrapper sources `~/.claude/secrets/secrets.env` for `PIHOLE_URL` and `PIHOLE_PASSWORD`, then invokes `uv run`.

## Development

- Run tests: `uv run pytest`
- Coverage: `uv run pytest --cov --cov-report=term`
- Python: 3.12+

## Relation to chris2ao-unifi-mcp

Same stack (FastMCP, httpx, Pydantic-settings, hatchling, uv) and the same module-per-capability layout under `src/pihole_mcp/tools/`. Simpler than unifi-mcp because Pi-hole is a single product (no dynamic product loading or discovery).

See [CHANGELOG.md](./CHANGELOG.md) for release notes.

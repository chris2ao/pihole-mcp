# pihole-mcp

[![test](https://github.com/chris2ao/pihole-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/chris2ao/pihole-mcp/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-compatible-6E56CF.svg)](https://modelcontextprotocol.io/)
[![Pi-hole v6](https://img.shields.io/badge/Pi--hole-v6-96060C.svg)](https://docs.pi-hole.net/)

Unified Pi-hole v6 MCP server. Consolidates the useful tools from three upstream MCPs (`aplaceforallmystuff/mcp-pihole`, `sbarbett/pihole-mcp-server`, `cwdcwd/mcp-server-pihole`) into one Python server that matches the `chris2ao-unifi-mcp` stack (FastMCP + httpx + Pydantic v2).

## Tools (28)

Stats (8): `get_stats`, `get_top_blocked`, `get_top_permitted`, `get_top_clients`, `get_query_types`, `get_forward_destinations`, `get_recent_blocked`, `get_history`

Queries (2): `get_query_log` (rich filters: time range, domain, client, upstream, cursor), `get_query_suggestions`

Blocking (3): `get_blocking_status`, `enable_blocking`, `disable_blocking` (with optional timer)

Domain lists (6): `get_whitelist`, `get_blacklist`, `add_to_whitelist`, `add_to_blacklist`, `remove_from_whitelist`, `remove_from_blacklist`

Local DNS (5): `list_local_dns`, `add_local_a_record`, `remove_local_a_record`, `add_local_cname_record`, `remove_local_cname_record`

Maintenance (4): `update_gravity`, `flush_cache`, `flush_logs`, `get_tail_log`

Plus `server_info`.

See `docs/plans/consolidated-tool-map.md` for per-tool endpoint mapping.

## Auth

Pi-hole v6 uses session-based auth. This server handles it automatically:

1. `POST /api/auth` with `{"password": "<app-password>"}` returns a session SID.
2. All subsequent calls include `X-FTL-SID: <sid>`.
3. On 401 or near-expiry, the client re-authenticates and retries once.
4. On shutdown, `DELETE /api/auth` releases the session.

**App password** is created in the Pi-hole Web UI: Settings > Web Interface > "Application password" > Generate. This is separate from the main admin web password and is the correct credential for API clients.

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

Same stack (FastMCP, httpx, Pydantic-settings, hatchling, uv). Simpler than unifi-mcp because Pi-hole is a single product (no dynamic product loading or discovery). If you extend this for multi-Pi-hole or for the gap items (adlist/gravity CRUD, groups, DHCP, Teleporter), follow the unifi-mcp module-per-capability pattern.

# Consolidated Pi-hole MCP: Tool Map

Superset of tools from three upstream Pi-hole MCP servers, mapped to Pi-hole v6 REST API.

## Upstream Sources

1. `aplaceforallmystuff/mcp-pihole` (TS, 14 tools, v6)
2. `sbarbett/pihole-mcp-server` (Python, 8 tools, v6, rich query filters + local DNS records)
3. `cwdcwd/mcp-server-pihole` (TS, 16 tools, v5+v6)

## Tool Surface (28 tools)

### Statistics (stats.py)

| Tool | Method | Endpoint | Params |
|------|--------|----------|--------|
| `get_stats` | GET | /api/stats/summary | — |
| `get_top_blocked` | GET | /api/stats/top_domains?blocked=true | `count` (int, default 10) |
| `get_top_permitted` | GET | /api/stats/top_domains?blocked=false | `count` (int, default 10) |
| `get_top_clients` | GET | /api/stats/top_clients | `count` (int, default 10), `blocked` (bool, default false) |
| `get_query_types` | GET | /api/stats/query_types | — |
| `get_forward_destinations` | GET | /api/stats/upstreams | — |
| `get_recent_blocked` | GET | /api/stats/recent_blocked | `count` (int, default 10) |
| `get_history` | GET | /api/history | — |

### Queries (queries.py)

| Tool | Method | Endpoint | Params |
|------|--------|----------|--------|
| `get_query_log` | GET | /api/queries | `length` (int, default 100), `from_ts`, `until_ts`, `domain`, `client_ip`, `upstream`, `cursor` |
| `get_query_suggestions` | GET | /api/queries/suggestions | — |

### Blocking Control (blocking.py)

| Tool | Method | Endpoint | Params |
|------|--------|----------|--------|
| `get_blocking_status` | GET | /api/dns/blocking | — |
| `enable_blocking` | POST | /api/dns/blocking | body: `{blocking: true}` |
| `disable_blocking` | POST | /api/dns/blocking | `duration_seconds` (int, optional); body `{blocking: false, timer: N}` |

### Domain Lists (domains.py)

| Tool | Method | Endpoint | Params |
|------|--------|----------|--------|
| `get_whitelist` | GET | /api/domains/allow/exact | — |
| `get_blacklist` | GET | /api/domains/deny/exact | — |
| `add_to_whitelist` | POST | /api/domains/allow/exact | `domain` (str), `comment` (str, optional) |
| `add_to_blacklist` | POST | /api/domains/deny/exact | `domain` (str), `comment` (str, optional) |
| `remove_from_whitelist` | DELETE | /api/domains/allow/exact/{domain} | `domain` (str) |
| `remove_from_blacklist` | DELETE | /api/domains/deny/exact/{domain} | `domain` (str) |

### Local DNS Records (local_dns.py)

| Tool | Method | Endpoint | Params |
|------|--------|----------|--------|
| `list_local_dns` | GET | /api/config/dns | — (returns hosts + cnameRecords) |
| `add_local_a_record` | PATCH | /api/config/dns | `host` (str), `ip` (str) |
| `remove_local_a_record` | PATCH | /api/config/dns | `host` (str) |
| `add_local_cname_record` | PATCH | /api/config/dns | `host` (str), `target` (str), `ttl` (int, default 300) |
| `remove_local_cname_record` | PATCH | /api/config/dns | `host` (str) |

Note: `/api/config/dns` uses PATCH with a delta on the `hosts` and `cnameRecords` arrays.

### Maintenance (maintenance.py)

| Tool | Method | Endpoint | Params |
|------|--------|----------|--------|
| `update_gravity` | POST | /api/action/gravity | — |
| `flush_cache` | POST | /api/action/flush/cache | — |
| `flush_logs` | POST | /api/action/flush/logs | — |
| `get_tail_log` | GET | /api/logs/dnsmasq | `lines` (int, default 100), `log` (str enum: dnsmasq/ftl/webserver, default dnsmasq) |

## Auth Pattern

- Config via env: `PIHOLE_URL`, `PIHOLE_PASSWORD` (app password), optional `PIHOLE_VERIFY_TLS` (default true)
- Session flow: POST `/api/auth` with `{"password": "..."}` → `{session: {sid, validity, csrf}}`
- Subsequent requests: `X-FTL-SID: <sid>` header
- Auto-refresh: if response 401 OR cached session within 60s of expiry, re-auth and retry once
- Session cache in-process; no persistence
- Logout on shutdown via `DELETE /api/auth` (best-effort)

## Design Decisions

- Single-instance only (v1). Multi-Pi-hole support (sbarbett pattern) deferred.
- No `pihole_` prefix on tool names; MCP namespace (`mcp__pihole__*`) already qualifies them.
- Destructive ops return structured JSON with the API response; no preview/apply pattern (those belong in skills, not MCP tools, per our homenet skills architecture).
- ASCII visualization from aplaceforallmystuff is NOT ported; the model can render tables from structured JSON.

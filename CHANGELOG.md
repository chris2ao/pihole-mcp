# Changelog

## v1.1.0 (2026-10-18)

Expands coverage of the Pi-hole v6 REST API from 28 to 72 tools and fixes several bugs where tools silently did the wrong thing or failed. Tested against the FTL v6.8 API specification.

### Fixed

- `get_query_log`: the client filter was sent as `client`, which FTL ignores, so every client's queries came back. It now sends `client_ip`.
- `update_gravity`: the endpoint answers with plain text, which the client tried to decode as JSON. The tool now returns the last lines of gravity output and reports `busy` when a run is already in progress (HTTP 409, FTL v6.8+).
- `flush_cache`: called `/api/action/flush/cache`, which does not exist in Pi-hole v6. It now restarts the DNS resolver, which clears the cache.
- `get_tail_log`: the `lines` parameter was ignored by the API. Lines are now trimmed by the server, and the new `next_id` parameter returns only newer entries.
- Delete tools (`remove_from_whitelist`, `remove_from_blacklist`, and the new remove tools) returned an error after a successful delete because the empty 204 response failed output validation. They now return `{"success": true}`.

### Added

- **Long-term statistics**: `from_ts` and `until_ts` on the stats and history tools query the long-term database for any time range. New `get_client_history` for per-client time series.
- **Query log filters**: `client_name`, `query_type`, `status`, `reply`, `dnssec`, `start`, and `disk`.
- **Domain search**: `search_domain` shows which list, regex, adlist, and group decides a domain's fate.
- **Regex and grouped domain lists**: `list_domains`, `add_domain`, `update_domain`, `remove_domain`.
- **Adlists**: `list_adlists`, `add_adlist`, `update_adlist`, `remove_adlist`.
- **Groups and clients** for per-device policy: `list_groups`, `add_group`, `update_group`, `remove_group`, `list_clients`, `get_client_suggestions`, `add_client`, `update_client`, `remove_client`.
- **System info**: `get_version`, `get_system_info`, `get_host_info`, `get_sensors`, `get_ftl_info`, `get_database_info`, `get_metrics`, `get_messages`, `delete_message`, `get_padd`.
- **Network and DHCP**: `list_network_devices`, `delete_network_device`, `get_gateway`, `get_routes`, `get_interfaces`, `list_dhcp_leases`, `remove_dhcp_lease`.
- **Settings**: `get_config`, `update_config`, `add_config_item`, `remove_config_item`.
- **Maintenance**: `restart_dns`, `flush_arp`, `flush_network`, `export_teleporter` (backup to a local zip).

### Security

- Disruptive tools preview by default and act only with `confirm=true`.
- `get_config` redacts password hashes and the TOTP secret, and settings tools refuse changes under `webserver.api`.
- Teleporter import is not exposed.
- Pi-hole FTL v6.6 through v6.8 fixed several API security advisories. Running FTL v6.8 or later is recommended.

### Changed

- Package version aligned with the release tag (`pyproject.toml` previously said 0.1.0).

## v1.0.0

First public release: 28 tools consolidated from three upstream Pi-hole MCP servers.

import time
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient
from pihole_mcp.errors import PiholeAPIError
from pihole_mcp.tools._common import preview


def register(mcp: FastMCP, client: PiholeClient) -> int:
    @mcp.tool()
    async def update_gravity(output_lines: int = 20) -> dict:
        """Refresh Pi-hole gravity (download adlists). Takes a minute or more.

        Returns the last output_lines lines of the gravity run. Reports cleanly if a run is already in progress.
        """
        try:
            result = await client.post("/action/gravity", params={"color": "false"})
        except PiholeAPIError as exc:
            if exc.status_code == 409:
                return {"status": "busy", "message": "A gravity update is already running. Try again when it finishes."}
            raise
        lines = ((result or {}).get("text") or "").strip().splitlines()
        return {"status": "done", "output": lines[-output_lines:]}

    @mcp.tool()
    async def flush_cache() -> dict:
        """Flush the DNS cache. Pi-hole v6 has no separate cache-flush endpoint, so this restarts the DNS resolver."""
        return await client.post("/action/restartdns")

    @mcp.tool()
    async def restart_dns(confirm: bool = False) -> dict:
        """Restart the DNS resolver (brief DNS outage, clears cache). Preview unless confirm=true."""
        if not confirm:
            return preview("restart_dns", impact="DNS resolution pauses for a few seconds")
        return await client.post("/action/restartdns")

    @mcp.tool()
    async def flush_logs() -> dict:
        """Clear the Pi-hole query log."""
        return await client.post("/action/flush/logs")

    @mcp.tool()
    async def flush_arp(confirm: bool = False) -> dict:
        """Flush the ARP cache of the Pi-hole host. Preview unless confirm=true."""
        if not confirm:
            return preview("flush_arp")
        return await client.post("/action/flush/arp")

    @mcp.tool()
    async def flush_network(confirm: bool = False) -> dict:
        """Clear Pi-hole's network device table (device history is lost). Preview unless confirm=true."""
        if not confirm:
            return preview("flush_network", impact="All network table entries are deleted")
        return await client.post("/action/flush/network")

    @mcp.tool()
    async def get_tail_log(
        lines: int = 100,
        log: Literal["dnsmasq", "ftl", "webserver"] = "dnsmasq",
        next_id: int | None = None,
    ) -> dict:
        """Get the last `lines` entries of a Pi-hole log ('dnsmasq', 'ftl', 'webserver').

        Pass next_id from a previous response to get only newer entries.
        """
        params = {"nextID": next_id} if next_id is not None else None
        result = await client.get(f"/logs/{log}", params=params) or {}
        entries = result.get("log") or []
        return {**result, "log": entries[-lines:] if lines > 0 else entries}

    @mcp.tool()
    async def export_teleporter(output_dir: str) -> dict:
        """Download a Teleporter backup zip of all Pi-hole settings and lists into output_dir.

        The archive contains the password hash, so store it securely. Existing files are never overwritten.
        """
        directory = Path(output_dir).expanduser().resolve()
        if not directory.is_dir():
            raise ValueError(f"output_dir does not exist or is not a directory: {directory}")
        target = directory / f"pihole-teleporter-{time.strftime('%Y%m%d-%H%M%S')}.zip"
        if target.exists():
            raise ValueError(f"Refusing to overwrite existing file: {target}")
        data = await client.get_bytes("/teleporter")
        target.write_bytes(data)
        return {"path": str(target), "bytes": len(data)}

    return 8

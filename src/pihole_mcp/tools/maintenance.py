from typing import Literal

from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient


def register(mcp: FastMCP, client: PiholeClient) -> int:
    @mcp.tool()
    async def update_gravity() -> dict:
        """Refresh Pi-hole gravity (adlist database). Takes a minute or more to complete."""
        return await client.post("/action/gravity")

    @mcp.tool()
    async def flush_cache() -> dict:
        """Flush the Pi-hole DNS cache."""
        return await client.post("/action/flush/cache")

    @mcp.tool()
    async def flush_logs() -> dict:
        """Clear the Pi-hole query log."""
        return await client.post("/action/flush/logs")

    @mcp.tool()
    async def get_tail_log(
        lines: int = 100,
        log: Literal["dnsmasq", "ftl", "webserver"] = "dnsmasq",
    ) -> dict:
        """Get the tail of a Pi-hole log file. log must be one of 'dnsmasq', 'ftl', 'webserver'."""
        return await client.get(f"/logs/{log}", params={"lines": lines})

    return 4

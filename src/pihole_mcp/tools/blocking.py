from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient


def register(mcp: FastMCP, client: PiholeClient) -> int:
    @mcp.tool()
    async def get_blocking_status() -> dict:
        """Check if Pi-hole DNS blocking is enabled. Returns status and any active timer."""
        return await client.get("/dns/blocking")

    @mcp.tool()
    async def enable_blocking() -> dict:
        """Enable DNS blocking immediately."""
        return await client.post("/dns/blocking", json={"blocking": True})

    @mcp.tool()
    async def disable_blocking(duration_seconds: int | None = None) -> dict:
        """Disable DNS blocking. If duration_seconds is given, re-enables after that timer; otherwise indefinite."""
        body: dict = {"blocking": False}
        if duration_seconds is not None:
            body["timer"] = duration_seconds
        return await client.post("/dns/blocking", json=body)

    return 3

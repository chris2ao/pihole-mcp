from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient


def register(mcp: FastMCP, client: PiholeClient) -> int:
    @mcp.tool()
    async def get_version() -> dict:
        """Installed and latest available versions of Pi-hole core, web, FTL, and Docker tag."""
        return await client.get("/info/version")

    @mcp.tool()
    async def get_system_info() -> dict:
        """Host uptime, memory, swap, CPU load, and process count."""
        return await client.get("/info/system")

    @mcp.tool()
    async def get_host_info() -> dict:
        """Host hardware model, kernel, and OS details."""
        return await client.get("/info/host")

    @mcp.tool()
    async def get_sensors() -> dict:
        """Temperature sensor readings and the configured hot limit."""
        return await client.get("/info/sensors")

    @mcp.tool()
    async def get_ftl_info() -> dict:
        """FTL process status: PID, uptime, privacy level, client and gravity counts, query frequency."""
        return await client.get("/info/ftl")

    @mcp.tool()
    async def get_database_info() -> dict:
        """Long-term query database size, query count, and SQLite version."""
        return await client.get("/info/database")

    @mcp.tool()
    async def get_metrics() -> dict:
        """DNS cache and DHCP metrics (cache size, insertions, evictions, reply types)."""
        return await client.get("/info/metrics")

    @mcp.tool()
    async def get_messages() -> dict:
        """Pi-hole diagnostic warnings (rate limiting, load, DNSMASQ errors, list issues)."""
        return await client.get("/info/messages")

    @mcp.tool()
    async def delete_message(message_id: int) -> dict:
        """Dismiss one diagnostic message by ID."""
        return await client.delete(f"/info/messages/{int(message_id)}")

    @mcp.tool()
    async def get_padd(full: bool = False) -> dict:
        """Compact dashboard in one call (PADD data): blocking, stats, top items, system, versions."""
        return await client.get("/padd", params={"full": "true"} if full else None)

    return 10

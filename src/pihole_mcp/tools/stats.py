from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient


def register(mcp: FastMCP, client: PiholeClient) -> int:
    @mcp.tool()
    async def get_stats() -> dict:
        """Get summary statistics (total queries, blocked queries, blocking percentage, unique domains, clients)."""
        return await client.get("/stats/summary")

    @mcp.tool()
    async def get_top_blocked(count: int = 10) -> dict:
        """Get top blocked domains by query count."""
        return await client.get("/stats/top_domains", params={"blocked": "true", "count": count})

    @mcp.tool()
    async def get_top_permitted(count: int = 10) -> dict:
        """Get top allowed (permitted) domains by query count."""
        return await client.get("/stats/top_domains", params={"blocked": "false", "count": count})

    @mcp.tool()
    async def get_top_clients(count: int = 10, blocked: bool = False) -> dict:
        """Get top clients by query count. Set blocked=true for top clients by blocked query count."""
        params: dict = {"count": count}
        if blocked:
            params["blocked"] = "true"
        return await client.get("/stats/top_clients", params=params)

    @mcp.tool()
    async def get_query_types() -> dict:
        """Breakdown of DNS query types (A, AAAA, PTR, SRV, etc)."""
        return await client.get("/stats/query_types")

    @mcp.tool()
    async def get_forward_destinations() -> dict:
        """Upstream DNS server stats (which forwarders served how many queries)."""
        return await client.get("/stats/upstreams")

    @mcp.tool()
    async def get_recent_blocked(count: int = 10) -> dict:
        """Recently blocked domains."""
        return await client.get("/stats/recent_blocked", params={"count": count})

    @mcp.tool()
    async def get_history() -> dict:
        """Time-series activity graph: timestamps, allowed/blocked/other counts per bucket."""
        return await client.get("/history")

    return 8

from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient


def register(mcp: FastMCP, client: PiholeClient) -> int:
    @mcp.tool()
    async def get_query_log(
        length: int = 100,
        from_ts: int | None = None,
        until_ts: int | None = None,
        domain: str | None = None,
        client_ip: str | None = None,
        upstream: str | None = None,
        cursor: str | None = None,
    ) -> dict:
        """Fetch recent DNS queries with optional filters.

        Filters:
        - length: number of queries (default 100)
        - from_ts / until_ts: Unix timestamps
        - domain: exact or wildcard (*) domain match
        - client_ip: exact or wildcard (*) client IP match
        - upstream: one of 'cache', 'blocklist', 'permitted'
        - cursor: pagination cursor from previous response
        """
        params: dict = {"length": length}
        if from_ts is not None:
            params["from"] = from_ts
        if until_ts is not None:
            params["until"] = until_ts
        if domain:
            params["domain"] = domain
        if client_ip:
            params["client"] = client_ip
        if upstream:
            params["upstream"] = upstream
        if cursor:
            params["cursor"] = cursor
        return await client.get("/queries", params=params)

    @mcp.tool()
    async def get_query_suggestions() -> dict:
        """Get available filter values for the query log (domains, clients, upstreams, types, statuses)."""
        return await client.get("/queries/suggestions")

    return 2

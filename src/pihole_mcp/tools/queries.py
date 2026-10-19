
from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient
from pihole_mcp.tools._common import compact


def register(mcp: FastMCP, client: PiholeClient) -> int:
    @mcp.tool()
    async def get_query_log(
        length: int = 100,
        from_ts: int | None = None,
        until_ts: int | None = None,
        domain: str | None = None,
        client_ip: str | None = None,
        client_name: str | None = None,
        upstream: str | None = None,
        query_type: str | None = None,
        status: str | None = None,
        reply: str | None = None,
        dnssec: str | None = None,
        start: int | None = None,
        cursor: int | None = None,
        disk: bool = False,
    ) -> dict:
        """Fetch DNS queries with optional filters (wildcards * supported on text filters).

        Filters:
        - length: number of queries (default 100); start: offset for paging
        - from_ts / until_ts: Unix timestamps
        - domain, client_ip, client_name, upstream: exact or wildcard match
        - query_type: e.g. A, AAAA, HTTPS, PTR (unmapped types appear as TYPEnnn or OTHER)
        - status: e.g. GRAVITY, FORWARDED, CACHE, REGEX, DENYLIST
        - reply: e.g. IP, NXDOMAIN, NODATA, CNAME
        - dnssec: e.g. SECURE, INSECURE, BOGUS
        - cursor: cursor value from a previous response
        - disk: true searches the long-term database instead of in-memory queries
        Valid filter values come from get_query_suggestions.
        """
        params = compact({
            "length": length,
            "from": from_ts,
            "until": until_ts,
            "domain": domain,
            "client_ip": client_ip,
            "client_name": client_name,
            "upstream": upstream,
            "type": query_type,
            "status": status,
            "reply": reply,
            "dnssec": dnssec,
            "start": start,
            "cursor": cursor,
        })
        if disk:
            params["disk"] = "true"
        return await client.get("/queries", params=params)

    @mcp.tool()
    async def get_query_suggestions() -> dict:
        """Get available filter values for the query log (domains, clients, upstreams, types, statuses)."""
        return await client.get("/queries/suggestions")

    return 2



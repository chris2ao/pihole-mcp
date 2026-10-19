from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient
from pihole_mcp.errors import PiholeError
from pihole_mcp.tools._common import compact


def _route(path: str, from_ts: int | None, until_ts: int | None) -> tuple[str, dict]:
    """Use the long-term database variant of a stats endpoint when a time range is given."""
    if from_ts is None and until_ts is None:
        return path, {}
    if from_ts is None or until_ts is None:
        raise PiholeError("from_ts and until_ts must be given together")
    prefix, _, rest = path.lstrip("/").partition("/")
    db_path = f"/{prefix}/database/{rest}" if rest else f"/{prefix}/database"
    return db_path, {"from": from_ts, "until": until_ts}


def register(mcp: FastMCP, client: PiholeClient) -> int:
    async def _get(path: str, from_ts: int | None, until_ts: int | None, **params) -> dict:
        target, range_params = _route(path, from_ts, until_ts)
        return await client.get(target, params=compact({**params, **range_params}) or None)

    @mcp.tool()
    async def get_stats(from_ts: int | None = None, until_ts: int | None = None) -> dict:
        """Summary statistics (total/blocked queries, percentage, unique domains, clients).

        Pass from_ts and until_ts (Unix timestamps) to query the long-term database for any range.
        """
        return await _get("/stats/summary", from_ts, until_ts)

    @mcp.tool()
    async def get_top_blocked(
        count: int = 10, from_ts: int | None = None, until_ts: int | None = None
    ) -> dict:
        """Top blocked domains by query count. from_ts/until_ts switch to the long-term database."""
        return await _get("/stats/top_domains", from_ts, until_ts, blocked="true", count=count)

    @mcp.tool()
    async def get_top_permitted(
        count: int = 10, from_ts: int | None = None, until_ts: int | None = None
    ) -> dict:
        """Top allowed domains by query count. from_ts/until_ts switch to the long-term database."""
        return await _get("/stats/top_domains", from_ts, until_ts, blocked="false", count=count)

    @mcp.tool()
    async def get_top_clients(
        count: int = 10,
        blocked: bool = False,
        from_ts: int | None = None,
        until_ts: int | None = None,
    ) -> dict:
        """Top clients by query count (blocked=true ranks by blocked queries). from_ts/until_ts use the long-term database."""
        return await _get(
            "/stats/top_clients", from_ts, until_ts,
            count=count, blocked="true" if blocked else None,
        )

    @mcp.tool()
    async def get_query_types(from_ts: int | None = None, until_ts: int | None = None) -> dict:
        """Breakdown of DNS query types (A, AAAA, PTR, SRV, etc). from_ts/until_ts use the long-term database."""
        return await _get("/stats/query_types", from_ts, until_ts)

    @mcp.tool()
    async def get_forward_destinations(
        from_ts: int | None = None, until_ts: int | None = None
    ) -> dict:
        """Upstream DNS server stats (which forwarders served how many queries). from_ts/until_ts use the long-term database."""
        return await _get("/stats/upstreams", from_ts, until_ts)

    @mcp.tool()
    async def get_recent_blocked(count: int = 10) -> dict:
        """Recently blocked domains."""
        return await client.get("/stats/recent_blocked", params={"count": count})

    @mcp.tool()
    async def get_history(from_ts: int | None = None, until_ts: int | None = None) -> dict:
        """Time-series activity: allowed/blocked/other counts per bucket. from_ts/until_ts use the long-term database."""
        return await _get("/history", from_ts, until_ts)

    @mcp.tool()
    async def get_client_history(
        count: int = 20, from_ts: int | None = None, until_ts: int | None = None
    ) -> dict:
        """Per-client query time series for the top `count` clients (0 = all).

        from_ts/until_ts query the long-term database instead (count is then ignored).
        """
        if from_ts is None and until_ts is None:
            return await client.get("/history/clients", params={"N": count})
        return await _get("/history/clients", from_ts, until_ts)

    return 9

from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient
from pihole_mcp.tools import (
    blocking,
    domains,
    local_dns,
    maintenance,
    queries,
    stats,
)


def register_all(mcp: FastMCP, client: PiholeClient) -> int:
    """Register every tool module against the FastMCP instance. Returns tool count."""
    count = 0
    for module in (stats, queries, blocking, domains, local_dns, maintenance):
        count += module.register(mcp, client)
    return count

from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient
from pihole_mcp.tools import (
    blocking,
    domains,
    groups,
    info,
    lists,
    local_dns,
    maintenance,
    network,
    queries,
    search,
    settings,
    stats,
)

MODULES = (
    stats, queries, blocking, domains, local_dns, maintenance,
    search, lists, groups, info, network, settings,
)


def register_all(mcp: FastMCP, client: PiholeClient) -> int:
    """Register every tool module against the FastMCP instance. Returns tool count."""
    count = 0
    for module in MODULES:
        count += module.register(mcp, client)
    return count

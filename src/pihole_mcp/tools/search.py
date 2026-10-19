from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient
from pihole_mcp.tools._common import seg


def register(mcp: FastMCP, client: PiholeClient) -> int:
    @mcp.tool()
    async def search_domain(domain: str, partial: bool = False, max_results: int = 20) -> dict:
        """Explain why a domain is blocked or allowed: shows matching domain-list entries,
        regexes, and adlists (gravity), with the groups each applies to.

        partial=true also matches substrings. max_results caps results per category.
        """
        params = {"partial": "true" if partial else "false", "N": max_results}
        return await client.get(f"/search/{seg(domain)}", params=params)

    return 1

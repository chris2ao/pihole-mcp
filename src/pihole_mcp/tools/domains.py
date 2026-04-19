from urllib.parse import quote

from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient


def register(mcp: FastMCP, client: PiholeClient) -> int:
    @mcp.tool()
    async def get_whitelist() -> dict:
        """List all exact-match allowed domains."""
        return await client.get("/domains/allow/exact")

    @mcp.tool()
    async def get_blacklist() -> dict:
        """List all exact-match blocked domains."""
        return await client.get("/domains/deny/exact")

    @mcp.tool()
    async def add_to_whitelist(domain: str, comment: str | None = None) -> dict:
        """Add a domain to the allow list (whitelist)."""
        body: dict = {"domain": domain}
        if comment:
            body["comment"] = comment
        return await client.post("/domains/allow/exact", json=body)

    @mcp.tool()
    async def add_to_blacklist(domain: str, comment: str | None = None) -> dict:
        """Add a domain to the deny list (blacklist)."""
        body: dict = {"domain": domain}
        if comment:
            body["comment"] = comment
        return await client.post("/domains/deny/exact", json=body)

    @mcp.tool()
    async def remove_from_whitelist(domain: str) -> dict:
        """Remove a domain from the allow list."""
        return await client.delete(f"/domains/allow/exact/{quote(domain, safe='')}")

    @mcp.tool()
    async def remove_from_blacklist(domain: str) -> dict:
        """Remove a domain from the deny list."""
        return await client.delete(f"/domains/deny/exact/{quote(domain, safe='')}")

    return 6

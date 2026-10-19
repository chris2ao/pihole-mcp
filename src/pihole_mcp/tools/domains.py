from typing import Literal

from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient
from pihole_mcp.tools._common import compact, seg

DomainType = Literal["allow", "deny"]
DomainKind = Literal["exact", "regex"]


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
        return await client.delete(f"/domains/allow/exact/{seg(domain)}")

    @mcp.tool()
    async def remove_from_blacklist(domain: str) -> dict:
        """Remove a domain from the deny list."""
        return await client.delete(f"/domains/deny/exact/{seg(domain)}")

    @mcp.tool()
    async def list_domains(
        domain_type: DomainType | None = None, kind: DomainKind | None = None
    ) -> dict:
        """List domain-list entries, optionally narrowed to allow/deny and exact/regex.

        kind requires domain_type.
        """
        path = "/domains"
        if domain_type:
            path += f"/{domain_type}"
            if kind:
                path += f"/{kind}"
        return await client.get(path)

    @mcp.tool()
    async def add_domain(
        domain: str,
        domain_type: DomainType,
        kind: DomainKind = "exact",
        comment: str | None = None,
        groups: list[int] | None = None,
        enabled: bool = True,
    ) -> dict:
        """Add an exact domain or a regex to the allow or deny list. groups are group IDs (default group 0)."""
        body = compact({"domain": domain, "comment": comment, "groups": groups, "enabled": enabled})
        return await client.post(f"/domains/{domain_type}/{kind}", json=body)

    @mcp.tool()
    async def update_domain(
        domain: str,
        domain_type: DomainType,
        kind: DomainKind = "exact",
        new_type: DomainType | None = None,
        new_kind: DomainKind | None = None,
        comment: str | None = None,
        groups: list[int] | None = None,
        enabled: bool | None = None,
    ) -> dict:
        """Update a domain-list entry: move it between lists, change comment, groups, or enabled state."""
        current = await client.get(f"/domains/{domain_type}/{kind}/{seg(domain)}")
        entry = (current.get("domains") or [{}])[0]
        body = {
            "type": new_type or domain_type,
            "kind": new_kind or kind,
            "comment": comment if comment is not None else entry.get("comment"),
            "groups": groups if groups is not None else entry.get("groups", [0]),
            "enabled": enabled if enabled is not None else entry.get("enabled", True),
        }
        return await client.put(f"/domains/{domain_type}/{kind}/{seg(domain)}", json=body)

    @mcp.tool()
    async def remove_domain(
        domain: str, domain_type: DomainType, kind: DomainKind = "exact"
    ) -> dict:
        """Remove an exact domain or regex from the allow or deny list."""
        return await client.delete(f"/domains/{domain_type}/{kind}/{seg(domain)}")

    return 10

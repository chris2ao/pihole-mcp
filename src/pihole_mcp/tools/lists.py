from typing import Literal

from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient
from pihole_mcp.tools._common import compact, preview, seg

ListType = Literal["block", "allow"]


def register(mcp: FastMCP, client: PiholeClient) -> int:
    @mcp.tool()
    async def list_adlists(list_type: ListType | None = None) -> dict:
        """List subscribed adlists (block lists and allow lists) with status and domain counts."""
        return await client.get("/lists", params=compact({"type": list_type}) or None)

    @mcp.tool()
    async def add_adlist(
        address: str,
        list_type: ListType = "block",
        comment: str | None = None,
        groups: list[int] | None = None,
        enabled: bool = True,
    ) -> dict:
        """Subscribe to an adlist URL. Run update_gravity afterwards to download it."""
        if not address.startswith(("http://", "https://", "file://")):
            raise ValueError("address must be an http(s):// or file:// URL")
        body = compact({"address": address, "comment": comment, "groups": groups, "enabled": enabled})
        return await client.post("/lists", params={"type": list_type}, json=body)

    @mcp.tool()
    async def update_adlist(
        address: str,
        list_type: ListType = "block",
        comment: str | None = None,
        groups: list[int] | None = None,
        enabled: bool | None = None,
    ) -> dict:
        """Change an adlist's comment, groups, or enabled state. Run update_gravity to apply."""
        current = await client.get(f"/lists/{seg(address)}", params={"type": list_type})
        entry = (current.get("lists") or [{}])[0]
        body = {
            "type": list_type,
            "comment": comment if comment is not None else entry.get("comment"),
            "groups": groups if groups is not None else entry.get("groups", [0]),
            "enabled": enabled if enabled is not None else entry.get("enabled", True),
        }
        return await client.put(f"/lists/{seg(address)}", params={"type": list_type}, json=body)

    @mcp.tool()
    async def remove_adlist(address: str, list_type: ListType = "block", confirm: bool = False) -> dict:
        """Unsubscribe from an adlist. Preview unless confirm=true. Run update_gravity afterwards."""
        if not confirm:
            current = await client.get(f"/lists/{seg(address)}", params={"type": list_type})
            return preview("remove_adlist", target=current.get("lists"))
        return await client.delete(f"/lists/{seg(address)}", params={"type": list_type})

    return 4

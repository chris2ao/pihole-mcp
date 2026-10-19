from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient
from pihole_mcp.tools._common import compact, preview, seg


def register(mcp: FastMCP, client: PiholeClient) -> int:
    @mcp.tool()
    async def list_groups() -> dict:
        """List groups. Groups tie clients to domain lists and adlists for per-device policy."""
        return await client.get("/groups")

    @mcp.tool()
    async def add_group(name: str, comment: str | None = None, enabled: bool = True) -> dict:
        """Create a group."""
        return await client.post("/groups", json=compact({"name": name, "comment": comment, "enabled": enabled}))

    @mcp.tool()
    async def update_group(
        name: str,
        new_name: str | None = None,
        comment: str | None = None,
        enabled: bool | None = None,
    ) -> dict:
        """Rename a group or change its comment or enabled state."""
        current = await client.get(f"/groups/{seg(name)}")
        entry = (current.get("groups") or [{}])[0]
        body = {
            "name": new_name or name,
            "comment": comment if comment is not None else entry.get("comment"),
            "enabled": enabled if enabled is not None else entry.get("enabled", True),
        }
        return await client.put(f"/groups/{seg(name)}", json=body)

    @mcp.tool()
    async def remove_group(name: str, confirm: bool = False) -> dict:
        """Delete a group. Preview unless confirm=true."""
        if not confirm:
            current = await client.get(f"/groups/{seg(name)}")
            return preview("remove_group", target=current.get("groups"))
        return await client.delete(f"/groups/{seg(name)}")

    @mcp.tool()
    async def list_clients() -> dict:
        """List configured clients (IP, MAC, hostname, CIDR, or interface) and their groups."""
        return await client.get("/clients")

    @mcp.tool()
    async def get_client_suggestions(count: int | None = None) -> dict:
        """Clients seen on the network that are not yet configured, as candidates for add_client."""
        return await client.get("/clients/_suggestions", params=compact({"count": count}) or None)

    @mcp.tool()
    async def add_client(client_id: str, comment: str | None = None, groups: list[int] | None = None) -> dict:
        """Configure a client by IP, MAC, hostname, CIDR subnet, or :interface, and assign group IDs."""
        body = compact({"client": client_id, "comment": comment, "groups": groups})
        return await client.post("/clients", json=body)

    @mcp.tool()
    async def update_client(
        client_id: str, comment: str | None = None, groups: list[int] | None = None
    ) -> dict:
        """Change a configured client's comment or group IDs."""
        current = await client.get(f"/clients/{seg(client_id)}")
        entry = (current.get("clients") or [{}])[0]
        body = {
            "comment": comment if comment is not None else entry.get("comment"),
            "groups": groups if groups is not None else entry.get("groups", [0]),
        }
        return await client.put(f"/clients/{seg(client_id)}", json=body)

    @mcp.tool()
    async def remove_client(client_id: str) -> dict:
        """Remove a configured client (it falls back to the default group)."""
        return await client.delete(f"/clients/{seg(client_id)}")

    return 9

from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient
from pihole_mcp.tools._common import preview, seg


def register(mcp: FastMCP, client: PiholeClient) -> int:
    @mcp.tool()
    async def list_network_devices(max_devices: int = 50, max_addresses: int = 3) -> dict:
        """Pi-hole's network table: MAC address, vendor, IPs, hostnames, first/last seen, query count."""
        return await client.get(
            "/network/devices", params={"max_devices": max_devices, "max_addresses": max_addresses}
        )

    @mcp.tool()
    async def delete_network_device(device_id: int, confirm: bool = False) -> dict:
        """Remove one device from the network table by its ID. Preview unless confirm=true."""
        if not confirm:
            return preview("delete_network_device", device_id=device_id)
        return await client.delete(f"/network/devices/{int(device_id)}")

    @mcp.tool()
    async def get_gateway(detailed: bool = False) -> dict:
        """Default gateway address and interface (detailed=true includes routes and interfaces)."""
        return await client.get("/network/gateway", params={"detailed": "true"} if detailed else None)

    @mcp.tool()
    async def get_routes(detailed: bool = False) -> dict:
        """Routing table of the Pi-hole host."""
        return await client.get("/network/routes", params={"detailed": "true"} if detailed else None)

    @mcp.tool()
    async def get_interfaces(detailed: bool = False) -> dict:
        """Network interfaces of the Pi-hole host with addresses and traffic counters."""
        return await client.get("/network/interfaces", params={"detailed": "true"} if detailed else None)

    @mcp.tool()
    async def list_dhcp_leases() -> dict:
        """Active DHCP leases (only populated when Pi-hole's DHCP server is enabled)."""
        return await client.get("/dhcp/leases")

    @mcp.tool()
    async def remove_dhcp_lease(ip: str, confirm: bool = False) -> dict:
        """Remove a DHCP lease by IP. Preview unless confirm=true."""
        if not confirm:
            return preview("remove_dhcp_lease", ip=ip)
        return await client.delete(f"/dhcp/leases/{seg(ip)}")

    return 7

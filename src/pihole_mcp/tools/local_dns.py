from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient


async def _current_dns_config(client: PiholeClient) -> dict:
    payload = await client.get("/config/dns")
    config = payload.get("config") or {}
    dns = config.get("dns") or {}
    return dns


async def _patch_dns(client: PiholeClient, dns_delta: dict) -> dict:
    return await client.patch("/config/dns", json={"config": {"dns": dns_delta}})


def register(mcp: FastMCP, client: PiholeClient) -> int:
    @mcp.tool()
    async def list_local_dns() -> dict:
        """List local DNS entries (hosts and CNAME records)."""
        dns = await _current_dns_config(client)
        return {"hosts": dns.get("hosts", []), "cnameRecords": dns.get("cnameRecords", [])}

    @mcp.tool()
    async def add_local_a_record(host: str, ip: str) -> dict:
        """Add a local A record (host -> IP). Replaces any existing entry for the same host."""
        dns = await _current_dns_config(client)
        hosts = [h for h in dns.get("hosts", []) if not h.endswith(f" {host}")]
        hosts.append(f"{ip} {host}")
        return await _patch_dns(client, {"hosts": hosts})

    @mcp.tool()
    async def remove_local_a_record(host: str) -> dict:
        """Remove any local A record matching the given host."""
        dns = await _current_dns_config(client)
        hosts = [h for h in dns.get("hosts", []) if not h.endswith(f" {host}")]
        return await _patch_dns(client, {"hosts": hosts})

    @mcp.tool()
    async def add_local_cname_record(host: str, target: str, ttl: int = 300) -> dict:
        """Add a local CNAME record (host -> target). Replaces any existing CNAME for the same host."""
        dns = await _current_dns_config(client)
        records = [r for r in dns.get("cnameRecords", []) if not r.startswith(f"{host},")]
        records.append(f"{host},{target},{ttl}")
        return await _patch_dns(client, {"cnameRecords": records})

    @mcp.tool()
    async def remove_local_cname_record(host: str) -> dict:
        """Remove any local CNAME record for the given host."""
        dns = await _current_dns_config(client)
        records = [r for r in dns.get("cnameRecords", []) if not r.startswith(f"{host},")]
        return await _patch_dns(client, {"cnameRecords": records})

    return 5

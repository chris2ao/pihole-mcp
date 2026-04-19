import asyncio

from fastmcp import FastMCP

from pihole_mcp import __version__
from pihole_mcp.client import PiholeClient
from pihole_mcp.config import PiholeConfig
from pihole_mcp.tools import register_all

mcp = FastMCP("chris2ao-pihole-mcp")

_config = PiholeConfig()
_client = PiholeClient(_config)

_tool_count = register_all(mcp, _client)


@mcp.tool()
def server_info() -> dict:
    """Return chris2ao-pihole-mcp server version, configured Pi-hole URL, and tool count."""
    return {
        "name": "chris2ao-pihole-mcp",
        "version": __version__,
        "pihole_url": _config.url,
        "api_base": _config.api_base,
        "tool_count": _tool_count + 1,
    }


def main() -> None:
    try:
        mcp.run()
    finally:
        try:
            asyncio.run(_client.close())
        except RuntimeError:
            pass

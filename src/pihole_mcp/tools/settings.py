from typing import Any

from fastmcp import FastMCP

from pihole_mcp.client import PiholeClient
from pihole_mcp.tools._common import preview, seg

# Secret-bearing keys are never returned to the model and never written through this server.
_SECRET_KEYS = {"pwhash", "app_pwhash", "totp_secret", "password"}
_BLOCKED_PREFIX = "webserver.api"


def redact(node: Any) -> Any:
    """Return a copy with secret-bearing keys masked."""
    if isinstance(node, dict):
        return {
            k: ("<redacted>" if k in _SECRET_KEYS and v not in ("", None) else redact(v))
            for k, v in node.items()
        }
    if isinstance(node, list):
        return [redact(v) for v in node]
    return node


def _parts(element: str) -> list[str]:
    parts = [p for p in element.replace("/", ".").split(".") if p]
    if not parts:
        raise ValueError("element must name a config path, e.g. 'dns.upstreams'")
    return parts


def _guard(parts: list[str]) -> None:
    dotted = ".".join(parts)
    if dotted.startswith(_BLOCKED_PREFIX) or _SECRET_KEYS.intersection(parts):
        raise ValueError(f"Refusing to modify '{dotted}': authentication settings are off limits")


def _nest(parts: list[str], value: Any) -> dict:
    node: Any = value
    for key in reversed(parts):
        node = {key: node}
    return node


def register(mcp: FastMCP, client: PiholeClient) -> int:
    async def _current(parts: list[str]) -> Any:
        return redact(await client.get("/config/" + "/".join(seg(p) for p in parts)))

    @mcp.tool()
    async def get_config(element: str | None = None, detailed: bool = False) -> dict:
        """Read Pi-hole settings. element narrows to a section or key, e.g. 'dns', 'dns.upstreams', 'dhcp'.

        detailed=true adds descriptions, allowed values, and defaults. Password hashes and the TOTP secret are redacted.
        """
        params = {"detailed": "true"} if detailed else None
        path = "/config" + ("/" + "/".join(seg(p) for p in _parts(element)) if element else "")
        return redact(await client.get(path, params=params))

    @mcp.tool()
    async def update_config(element: str, value: Any, restart: bool = True, confirm: bool = False) -> dict:
        """Set a Pi-hole setting, e.g. element='dns.upstreams', value=['9.9.9.9'].

        Preview (current value) unless confirm=true. Some settings restart FTL; restart=false defers that.
        Authentication settings (webserver.api.*) are refused.
        """
        parts = _parts(element)
        _guard(parts)
        if not confirm:
            return preview("update_config", element=".".join(parts), current=await _current(parts), new=value)
        return redact(await client.patch(
            "/config", params={"restart": str(restart).lower()}, json={"config": _nest(parts, value)}
        ))

    @mcp.tool()
    async def add_config_item(element: str, value: str, restart: bool = True, confirm: bool = False) -> dict:
        """Append one value to an array setting, e.g. element='dns.upstreams', value='1.1.1.1'. Preview unless confirm=true."""
        parts = _parts(element)
        _guard(parts)
        if not confirm:
            return preview("add_config_item", element=".".join(parts), current=await _current(parts), add=value)
        path = "/config/" + "/".join(seg(p) for p in parts) + f"/{seg(value)}"
        return await client.put(path, params={"restart": str(restart).lower()})

    @mcp.tool()
    async def remove_config_item(element: str, value: str, restart: bool = True, confirm: bool = False) -> dict:
        """Remove one value from an array setting. Preview unless confirm=true."""
        parts = _parts(element)
        _guard(parts)
        if not confirm:
            return preview("remove_config_item", element=".".join(parts), current=await _current(parts), remove=value)
        path = "/config/" + "/".join(seg(p) for p in parts) + f"/{seg(value)}"
        return await client.delete(path, params={"restart": str(restart).lower()})

    return 4

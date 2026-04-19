class PiholeError(Exception):
    """Base error for Pi-hole MCP."""


class PiholeAuthError(PiholeError):
    """Authentication failed or session could not be established."""


class PiholeAPIError(PiholeError):
    """Pi-hole API returned a non-2xx response."""

    def __init__(self, status_code: int, message: str, body: object | None = None):
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.body = body

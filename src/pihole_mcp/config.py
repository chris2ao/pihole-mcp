from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PiholeConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PIHOLE_", case_sensitive=False)

    url: str = Field(..., description="Pi-hole base URL, e.g. http://pihole.lan or https://pihole.lan/admin")
    password: str = Field(..., description="Pi-hole app password (Settings > Web Interface > Application password)")
    verify_tls: bool = Field(default=True, description="Verify TLS cert on the Pi-hole URL")
    timeout_seconds: float = Field(default=10.0, description="HTTP request timeout")

    @property
    def api_base(self) -> str:
        base = self.url.rstrip("/")
        if base.endswith("/admin"):
            base = base[: -len("/admin")]
        return f"{base}/api"

from pihole_mcp.config import PiholeConfig


def test_api_base_strips_trailing_slash(monkeypatch):
    monkeypatch.setenv("PIHOLE_URL", "http://pihole.lan/")
    monkeypatch.setenv("PIHOLE_PASSWORD", "pw")
    c = PiholeConfig()
    assert c.api_base == "http://pihole.lan/api"


def test_api_base_strips_admin_suffix(monkeypatch):
    monkeypatch.setenv("PIHOLE_URL", "http://pihole.lan/admin")
    monkeypatch.setenv("PIHOLE_PASSWORD", "pw")
    c = PiholeConfig()
    assert c.api_base == "http://pihole.lan/api"


def test_api_base_preserves_https(monkeypatch):
    monkeypatch.setenv("PIHOLE_URL", "https://pi.example.com")
    monkeypatch.setenv("PIHOLE_PASSWORD", "pw")
    c = PiholeConfig()
    assert c.api_base == "https://pi.example.com/api"

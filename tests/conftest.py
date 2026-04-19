import os

import pytest

os.environ.setdefault("PIHOLE_URL", "http://pihole.test")
os.environ.setdefault("PIHOLE_PASSWORD", "test-app-password")


@pytest.fixture
def config():
    from pihole_mcp.config import PiholeConfig
    return PiholeConfig()


@pytest.fixture
async def client(config):
    from pihole_mcp.client import PiholeClient
    c = PiholeClient(config)
    yield c
    await c.close()

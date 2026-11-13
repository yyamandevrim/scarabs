"""Existing panel tests now exercise the authenticated production route."""
from fastapi.testclient import TestClient as RawClient
TEST_SECRET = 'unit-test-only-not-a-deployment-secret'

class TestClient(RawClient):
    __test__ = False
    def __enter__(self):
        client = super().__enter__()
        # Configure through the same local setting used in deployments, before login.
        self.app.state.panel_auth.secret = TEST_SECRET
        assert client.post('/api/auth/login', json={'secret': TEST_SECRET}).status_code == 200
        return client

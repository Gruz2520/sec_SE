from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_legacy_endpoint_is_gone():
    response = client.post("/items", params={"name": "test"})
    assert response.status_code == 410

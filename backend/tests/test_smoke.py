import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://familyman:familyman_test@localhost:5432/familyman_test",
)


def test_app_imports():
    from app.main import app

    assert app.title
    assert app.version


def test_health_endpoint():
    from fastapi.testclient import TestClient

    from app.main import app

    # Instantiate without the context manager so the DB lifespan is not
    # required for this pure health-check smoke test.
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

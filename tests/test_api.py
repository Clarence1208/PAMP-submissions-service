import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from app.main import app
from app.shared.database import get_session


# Test database setup
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///test.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_root_endpoint(client: TestClient):
    """Test the root endpoint"""
    response = client.get("/")
    data = response.json()
    assert response.status_code == 200
    assert "Welcome to PAMP Submissions Service" in data["message"]
    assert data["version"] == "1.0.0"


def test_health_check(client: TestClient):
    """Test health check endpoint"""
    response = client.get("/health/")
    data = response.json()
    assert response.status_code == 200
    assert data["status"] in ["healthy", "degraded"]
    assert "timestamp" in data
    assert data["version"] == "1.0.0"


def test_liveness_check(client: TestClient):
    """Test liveness endpoint"""
    response = client.get("/health/liveness")
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "alive"
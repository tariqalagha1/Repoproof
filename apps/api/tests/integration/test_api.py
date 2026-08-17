"""Integration tests — core API endpoints with an in-memory database."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.infrastructure.models import Base
from src.main import create_app


@pytest_asyncio.fixture
async def async_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine):
    session_factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    app = create_app()

    async def override_get_db():
        yield db_session

    from src.infrastructure.database import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ═══════════════════════════════════════════════════════════
# Health
# ═══════════════════════════════════════════════════════════

class TestHealth:
    async def test_health_ok(self, client):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    async def test_readiness(self, client):
        resp = await client.get("/api/v1/readiness")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"

    async def test_llm_status_structure(self, client):
        resp = await client.get("/api/v1/llm/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "provider" in data
        assert "status" in data


# ═══════════════════════════════════════════════════════════
# Projects
# ═══════════════════════════════════════════════════════════

class TestProjects:
    async def test_create_project(self, client):
        resp = await client.post("/api/v1/projects", json={"name": "Test", "description": "desc"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test"
        assert data["description"] == "desc"
        assert "id" in data

    async def test_list_projects(self, client):
        await client.post("/api/v1/projects", json={"name": "P1"})
        resp = await client.get("/api/v1/projects")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_project(self, client):
        created = await client.post("/api/v1/projects", json={"name": "P2"})
        pid = created.json()["id"]
        resp = await client.get(f"/api/v1/projects/{pid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "P2"

    async def test_get_project_not_found(self, client):
        resp = await client.get("/api/v1/projects/nonexistent")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════
# Verification Runs
# ═══════════════════════════════════════════════════════════

class TestRuns:
    async def test_create_run(self, client):
        proj = await client.post("/api/v1/projects", json={"name": "R"})
        pid = proj.json()["id"]
        resp = await client.post(f"/api/v1/projects/{pid}/runs", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["lifecycle_state"] == "created"
        assert data["project_id"] == pid

    async def test_list_runs(self, client):
        proj = await client.post("/api/v1/projects", json={"name": "R2"})
        pid = proj.json()["id"]
        await client.post(f"/api/v1/projects/{pid}/runs", json={})
        resp = await client.get(f"/api/v1/projects/{pid}/runs")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_transition_history(self, client):
        proj = await client.post("/api/v1/projects", json={"name": "R3"})
        pid = proj.json()["id"]
        run = await client.post(f"/api/v1/projects/{pid}/runs", json={})
        rid = run.json()["id"]
        await client.post(f"/api/v1/runs/{rid}/transitions", json={"from": "created", "to": "discovering"})
        resp = await client.get(f"/api/v1/runs/{rid}/transitions")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_checkpoints(self, client):
        proj = await client.post("/api/v1/projects", json={"name": "R4"})
        pid = proj.json()["id"]
        run = await client.post(f"/api/v1/projects/{pid}/runs", json={})
        rid = run.json()["id"]
        await client.post(f"/api/v1/runs/{rid}/checkpoints", json={"name": "cp1"})
        resp = await client.get(f"/api/v1/runs/{rid}/checkpoints")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


# ═══════════════════════════════════════════════════════════
# Repository Connections
# ═══════════════════════════════════════════════════════════

class TestRepositoryConnections:
    async def test_submit_valid_repo(self, client):
        resp = await client.post("/api/v1/repository-connections", json={
            "url": "https://github.com/nousresearch/hermes-agent",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["url"] == "https://github.com/nousresearch/hermes-agent"
        assert data["status"] == "valid"
        assert "id" in data

    async def test_submit_normalizes_dot_git(self, client):
        resp = await client.post("/api/v1/repository-connections", json={
            "url": "https://github.com/nousresearch/hermes-agent.git",
        })
        assert resp.status_code == 200
        assert resp.json()["url"] == "https://github.com/nousresearch/hermes-agent"

    async def test_submit_rejects_invalid_url(self, client):
        resp = await client.post("/api/v1/repository-connections", json={
            "url": "https://gitlab.com/a/b",
        })
        assert resp.status_code == 400

    async def test_list_connections(self, client):
        await client.post("/api/v1/repository-connections", json={
            "url": "https://github.com/a/b",
        })
        resp = await client.get("/api/v1/repository-connections")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_connection_by_id(self, client):
        created = await client.post("/api/v1/repository-connections", json={
            "url": "https://github.com/a/c",
        })
        cid = created.json()["id"]
        resp = await client.get(f"/api/v1/repository-connections/{cid}")
        assert resp.status_code == 200
        assert resp.json()["url"] == "https://github.com/a/c"


# ═══════════════════════════════════════════════════════════
# Gates
# ═══════════════════════════════════════════════════════════

class TestGates:
    async def test_list_gates_returns_six(self, client):
        resp = await client.get("/api/v1/gates")
        assert resp.status_code == 200
        gates = resp.json()
        assert len(gates) == 6
        assert all(g["status"] == "planned" for g in gates)


# ═══════════════════════════════════════════════════════════
# Compatibility Score
# ═══════════════════════════════════════════════════════════

class TestCompatibility:
    async def test_compatibility_structure(self, client):
        proj = await client.post("/api/v1/projects", json={"name": "C"})
        pid = proj.json()["id"]
        job = await client.post("/api/v1/master-jobs", json={
            "project_id": pid, "repository_url": "https://github.com/a/b",
        })
        jid = job.json()["id"]
        resp = await client.get(f"/api/v1/compatibility/{jid}")
        assert resp.status_code == 200
        data = resp.json()
        assert "overall" in data
        assert "breakdown" in data
        assert "security" in data["breakdown"]
        assert "tests" in data["breakdown"]

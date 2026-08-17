"""Integration tests — master jobs: creation, lifecycle, progress, environments."""

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


async def _make_job(client, name="Job"):
    proj = await client.post("/api/v1/projects", json={"name": name})
    pid = proj.json()["id"]
    job = await client.post("/api/v1/master-jobs", json={
        "project_id": pid, "repository_url": "https://github.com/a/b",
    })
    return job.json()["id"]


# ═══════════════════════════════════════════════════════════
# Master Job Creation
# ═══════════════════════════════════════════════════════════

class TestMasterJobCreation:
    async def test_create_job(self, client):
        jid = await _make_job(client)
        assert jid

        resp = await client.get(f"/api/v1/master-jobs/{jid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "created"
        assert "stages" in data

    async def test_list_jobs(self, client):
        await _make_job(client, "J1")
        await _make_job(client, "J2")
        resp = await client.get("/api/v1/master-jobs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_job_not_found(self, client):
        resp = await client.get("/api/v1/master-jobs/nonexistent")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════
# Job Lifecycle: pause / resume / cancel / intake
# ═══════════════════════════════════════════════════════════

class TestMasterJobLifecycle:
    async def test_pause_job(self, client):
        jid = await _make_job(client, "Pause")
        resp = await client.post(f"/api/v1/master-jobs/{jid}/pause", json={"reason": "test"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "paused"

    async def test_resume_job(self, client):
        jid = await _make_job(client, "Resume")
        await client.post(f"/api/v1/master-jobs/{jid}/pause", json={})
        resp = await client.post(f"/api/v1/master-jobs/{jid}/resume", json={})
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"

    async def test_cancel_job(self, client):
        jid = await _make_job(client, "Cancel")
        resp = await client.post(f"/api/v1/master-jobs/{jid}/cancel", json={})
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    async def test_complete_intake(self, client):
        jid = await _make_job(client, "Intake")
        resp = await client.post(f"/api/v1/master-jobs/{jid}/complete-intake", json={})
        assert resp.status_code == 200
        assert resp.json()["status"] == "discovering"

    async def test_progress_endpoint(self, client):
        jid = await _make_job(client, "Progress")
        resp = await client.get(f"/api/v1/master-jobs/{jid}/progress")
        assert resp.status_code == 200
        assert "progress" in resp.json()


# ═══════════════════════════════════════════════════════════
# Stages
# ═══════════════════════════════════════════════════════════

class TestStages:
    async def test_stages_endpoint_returns_list(self, client):
        jid = await _make_job(client, "Stages")
        resp = await client.get(f"/api/v1/master-jobs/{jid}/stages")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ═══════════════════════════════════════════════════════════
# Environment Provider Status
# ═══════════════════════════════════════════════════════════

class TestProviderStatus:
    async def test_provider_status(self, client):
        resp = await client.get("/api/v1/environments/provider-status")
        assert resp.status_code == 200
        data = resp.json()
        assert "provider" in data
        assert "available" in data

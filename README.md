# RepoProof AI

Automated software repository verification — connects to repositories, evaluates them through evidence-backed verification gates, identifies missing capabilities and risks, and recommends controlled upgrades.

## Quick Start

```bash
docker compose up -d
curl http://localhost:8000/api/v1/health
```

## Architecture

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: Next.js + TypeScript
- **Runner**: Docker-based isolated execution environments
- **LLM**: Provider-neutral abstraction with Hermes adapter

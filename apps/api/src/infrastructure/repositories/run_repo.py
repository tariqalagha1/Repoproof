"""Verification run repository."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    CheckpointModel,
    EvidenceItemModel,
    FindingModel,
    RunTransitionModel,
    VerificationRunModel,
)


class RunRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, project_id: str, branch: str = "", commit_hash: str = "") -> VerificationRunModel:
        run = VerificationRunModel(
            id=uuid4().hex,
            project_id=project_id,
            branch=branch,
            commit_hash=commit_hash,
        )
        self.session.add(run)
        await self.session.flush()
        return run

    async def get_by_id(self, run_id: str) -> VerificationRunModel | None:
        return await self.session.get(VerificationRunModel, run_id)

    async def list_by_project(self, project_id: str) -> list[VerificationRunModel]:
        result = await self.session.execute(
            select(VerificationRunModel).where(VerificationRunModel.project_id == project_id)
        )
        return list(result.scalars().all())

    async def update_lifecycle(self, run_id: str, new_state: str) -> VerificationRunModel | None:
        run = await self.get_by_id(run_id)
        if run:
            run.lifecycle = new_state
            await self.session.flush()
        return run

    # -- checkpoints --
    async def create_checkpoint(self, run_id: str, name: str, data: str = "") -> CheckpointModel:
        cp = CheckpointModel(id=uuid4().hex, run_id=run_id, name=name, data=data)
        self.session.add(cp)
        await self.session.flush()
        return cp

    async def list_checkpoints(self, run_id: str) -> list[CheckpointModel]:
        result = await self.session.execute(
            select(CheckpointModel).where(CheckpointModel.run_id == run_id)
        )
        return list(result.scalars().all())

    # -- transitions --
    async def add_transition(self, run_id: str, from_state: str, to_state: str) -> RunTransitionModel:
        t = RunTransitionModel(id=uuid4().hex, run_id=run_id, from_state=from_state, to_state=to_state)
        self.session.add(t)
        await self.session.flush()
        return t

    async def list_transitions(self, run_id: str) -> list[RunTransitionModel]:
        result = await self.session.execute(
            select(RunTransitionModel).where(RunTransitionModel.run_id == run_id)
        )
        return list(result.scalars().all())

    # -- findings --
    async def add_finding(self, run_id: str, severity: str, title: str, description: str) -> FindingModel:
        f = FindingModel(id=uuid4().hex, run_id=run_id, severity=severity, title=title, description=description)
        self.session.add(f)
        await self.session.flush()
        return f

    # -- evidence --
    async def add_evidence(self, run_id: str, type: str, content: str) -> EvidenceItemModel:
        e = EvidenceItemModel(id=uuid4().hex, run_id=run_id, type=type, content=content)
        self.session.add(e)
        await self.session.flush()
        return e

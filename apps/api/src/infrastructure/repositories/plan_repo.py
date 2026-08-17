"""Plan repository."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..plan_models import (
    CommandSpecificationModel,
    PlanConflictModel,
    PlanStageModel,
    VerificationPlanModel,
)


class PlanRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, master_job_id: str, ecosystem: str = "unknown") -> VerificationPlanModel:
        plan = VerificationPlanModel(
            id=uuid4().hex,
            master_job_id=master_job_id,
            ecosystem=ecosystem,
        )
        self.session.add(plan)
        await self.session.flush()
        return plan

    async def get_by_id(self, plan_id: str) -> VerificationPlanModel | None:
        return await self.session.get(VerificationPlanModel, plan_id)

    async def get_by_master_job(self, master_job_id: str) -> VerificationPlanModel | None:
        result = await self.session.execute(
            select(VerificationPlanModel).where(VerificationPlanModel.master_job_id == master_job_id)
        )
        return result.scalars().first()

    async def list_stages(self, plan_id: str) -> list[PlanStageModel]:
        result = await self.session.execute(
            select(PlanStageModel).where(PlanStageModel.plan_id == plan_id)
        )
        return list(result.scalars().all())

    async def add_stage(self, plan_id: str, name: str, seq: int, description: str = "") -> PlanStageModel:
        stage = PlanStageModel(id=uuid4().hex, plan_id=plan_id, name=name, seq=seq, description=description)
        self.session.add(stage)
        await self.session.flush()
        return stage

    async def add_command(self, stage_id: str, command: str) -> CommandSpecificationModel:
        cmd = CommandSpecificationModel(id=uuid4().hex, plan_stage_id=stage_id, command=command)
        self.session.add(cmd)
        await self.session.flush()
        return cmd

    async def list_commands(self, stage_id: str) -> list[CommandSpecificationModel]:
        result = await self.session.execute(
            select(CommandSpecificationModel).where(CommandSpecificationModel.plan_stage_id == stage_id)
        )
        return list(result.scalars().all())

    async def add_conflict(self, plan_id: str, description: str) -> PlanConflictModel:
        c = PlanConflictModel(id=uuid4().hex, plan_id=plan_id, description=description)
        self.session.add(c)
        await self.session.flush()
        return c

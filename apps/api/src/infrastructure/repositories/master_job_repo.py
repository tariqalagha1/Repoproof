"""Master verification job repository."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    ApprovalRequestModel,
    MasterVerificationJobModel,
    VerificationCheckModel,
    VerificationStageModel,
)
from ..discovery_models import ArchitectureManifestModel, DiscoveryClaimModel, DiscoveryWarningModel


class MasterJobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, project_id: str, repo_url: str, branch: str = "main") -> MasterVerificationJobModel:
        job = MasterVerificationJobModel(
            id=uuid4().hex,
            project_id=project_id,
            repo_url=repo_url,
            branch=branch,
        )
        self.session.add(job)
        await self.session.flush()

        # Seed the 16 pipeline stages from the canonical definitions
        from src.domain.enums import STAGE_DEFINITIONS
        for defn in STAGE_DEFINITIONS:
            self.session.add(VerificationStageModel(
                id=uuid4().hex,
                master_job_id=job.id,
                stage_type=defn["type"].value,
                seq=defn["seq"],
                status="pending",
                applicability=defn["applicability"].value,
                criticality=defn["criticality"].value,
            ))
        return job

    async def get_by_id(self, job_id: str) -> MasterVerificationJobModel | None:
        return await self.session.get(MasterVerificationJobModel, job_id)

    async def list_by_project(self, project_id: str) -> list[MasterVerificationJobModel]:
        result = await self.session.execute(
            select(MasterVerificationJobModel).where(MasterVerificationJobModel.project_id == project_id)
        )
        return list(result.scalars().all())

    # -- stages --
    async def get_stages(self, job_id: str) -> list[VerificationStageModel]:
        result = await self.session.execute(
            select(VerificationStageModel).where(VerificationStageModel.master_job_id == job_id)
        )
        return list(result.scalars().all())

    async def get_stage_by_id(self, stage_id: str) -> VerificationStageModel | None:
        return await self.session.get(VerificationStageModel, stage_id)

    async def create_stage(self, job_id: str, stage_type: str, seq: int) -> VerificationStageModel:
        stage = VerificationStageModel(
            id=uuid4().hex,
            master_job_id=job_id,
            stage_type=stage_type,
            seq=seq,
        )
        self.session.add(stage)
        await self.session.flush()
        return stage

    # -- checks --
    async def get_checks(self, stage_id: str) -> list[VerificationCheckModel]:
        result = await self.session.execute(
            select(VerificationCheckModel).where(VerificationCheckModel.stage_id == stage_id)
        )
        return list(result.scalars().all())

    async def add_check(self, stage_id: str, name: str, passed: bool = False) -> VerificationCheckModel:
        check = VerificationCheckModel(id=uuid4().hex, stage_id=stage_id, name=name, passed=passed)
        self.session.add(check)
        await self.session.flush()
        return check

    # -- lifecycle --
    async def complete_intake(self, job_id: str, repo_url: str, branch: str, commit_hash: str) -> MasterVerificationJobModel:
        job = await self.get_by_id(job_id)
        if job:
            job.repo_url = repo_url
            job.branch = branch
            job.commit_hash = commit_hash
            job.status = "discovering"
            await self.session.flush()
        return job  # type: ignore[return-value]

    async def pause_job(self, job_id: str) -> MasterVerificationJobModel | None:
        job = await self.get_by_id(job_id)
        if job:
            job.status = "paused"
            await self.session.flush()
        return job

    async def resume_job(self, job_id: str) -> MasterVerificationJobModel | None:
        job = await self.get_by_id(job_id)
        if job:
            job.status = "running"
            await self.session.flush()
        return job

    async def cancel_job(self, job_id: str) -> MasterVerificationJobModel | None:
        job = await self.get_by_id(job_id)
        if job:
            job.status = "cancelled"
            await self.session.flush()
        return job

    # -- discovery --
    async def run_passive_discovery(self, job_id: str, manifest_data: dict) -> ArchitectureManifestModel:
        manifest = ArchitectureManifestModel(
            id=uuid4().hex,
            master_job_id=job_id,
            project_root=manifest_data.get("project_root", ""),
            entry_points=str(manifest_data.get("entry_points", [])),
            detected_frameworks=str(manifest_data.get("detected_frameworks", [])),
            detected_languages=str(manifest_data.get("detected_languages", [])),
            dependency_files=str(manifest_data.get("dependency_files", [])),
            file_count=manifest_data.get("file_count", 0),
            secrets_found=manifest_data.get("secrets_found", 0),
        )
        self.session.add(manifest)
        await self.session.flush()
        return manifest

    async def get_manifest(self, job_id: str) -> ArchitectureManifestModel | None:
        result = await self.session.execute(
            select(ArchitectureManifestModel).where(ArchitectureManifestModel.master_job_id == job_id)
        )
        return result.scalars().first()

    async def get_discovery_claims(self, job_id: str) -> list[DiscoveryClaimModel]:
        result = await self.session.execute(
            select(DiscoveryClaimModel).where(DiscoveryClaimModel.master_job_id == job_id)
        )
        return list(result.scalars().all())

    async def get_discovery_warnings(self, job_id: str) -> list[DiscoveryWarningModel]:
        result = await self.session.execute(
            select(DiscoveryWarningModel).where(DiscoveryWarningModel.master_job_id == job_id)
        )
        return list(result.scalars().all())

    # -- plan generation --
    async def run_plan_generation(self, job_id: str) -> MasterVerificationJobModel | None:
        job = await self.get_by_id(job_id)
        if job:
            job.status = "awaiting_approval"
            await self.session.flush()
        return job

    # -- policy validation --
    async def run_policy_validation(self, job_id: str) -> MasterVerificationJobModel | None:
        job = await self.get_by_id(job_id)
        if job:
            job.status = "running" if job.status not in ("cancelled", "failed") else job.status
            await self.session.flush()
        return job

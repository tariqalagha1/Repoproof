"""Project repository."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ProjectModel


class ProjectRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, org_id: str, name: str, description: str = "") -> ProjectModel:
        project = ProjectModel(
            id=uuid4().hex,
            org_id=org_id,
            name=name,
            description=description,
        )
        self.session.add(project)
        await self.session.flush()
        return project

    async def get_by_id(self, project_id: str) -> ProjectModel | None:
        return await self.session.get(ProjectModel, project_id)

    async def list_by_org(self, org_id: str) -> list[ProjectModel]:
        result = await self.session.execute(
            select(ProjectModel).where(ProjectModel.org_id == org_id)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[ProjectModel]:
        result = await self.session.execute(select(ProjectModel))
        return list(result.scalars().all())

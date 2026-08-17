"""Base repository."""

from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    model: type[T]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, instance: T) -> T:
        self.session.add(instance)
        await self.session.flush()
        return instance

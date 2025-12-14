from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import get_db


async def get_database() -> AsyncSession:
    async for db in get_db():
        yield db

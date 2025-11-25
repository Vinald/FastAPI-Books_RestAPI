from sqlmodel import create_engine, SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine
from .config import settings
from app.models.book import Book

engine = AsyncEngine(
    create_engine(
        url=settings.DATABASE_URL,
        echo=True
    )
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

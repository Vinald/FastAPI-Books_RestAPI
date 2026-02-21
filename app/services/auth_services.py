import uuid

from sqlalchemy.ext.asyncio import AsyncSession


class AuthService:
    @staticmethod
    async def login(session: AsyncSession):
        pass

    @staticmethod
    async def register(user_uuid: uuid.UUID, session: AsyncSession):
        pass

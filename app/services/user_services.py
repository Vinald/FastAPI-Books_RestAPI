import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate, UserUpdate


class UserService:
    @staticmethod
    async def get_all_user(session: AsyncSession):
        pass

    @staticmethod
    async def get_user_by_uuid(user_uuid: uuid.UUID, session: AsyncSession):
        pass

    @staticmethod
    async def get_user_by_email(email: str, session: AsyncSession):
        pass

    @staticmethod
    async def create_user(user_data: UserCreate, session: AsyncSession):
        pass

    async def update_user(self, user_uuid: uuid.UUID, update_data: UserUpdate, session: AsyncSession):
        pass

    async def delete_user(self, user_uuid: uuid.UUID, session: AsyncSession):
        pass

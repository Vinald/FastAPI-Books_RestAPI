from datetime import datetime
from sqlmodel import SQLModel, Field, Column
import uuid
import sqlalchemy.dialects.postgresql as postgresql

class Book(SQLModel, table=True):

    __tablename__ = "books"

    uid: uuid.UUID | None = Field(
        sa_column=Column(
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            default=uuid.uuid4
        ))
    title: str = Field(nullable=False)
    author: str = Field(nullable=False)
    publisher: str = Field(nullable=False)
    publish_date: str = Field(nullable=False)
    pages: int = Field(nullable=False)
    language: str = Field(nullable=False)
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP(),
            default=datetime.now,
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP(),
            default=datetime.now,
        )
    )

    def __repr__(self) -> str:
        return f"Book(uid={self.uid}, title={self.title}, author={self.author})"
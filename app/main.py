from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1.routes import book
from app.core.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Starting up the application...")
    yield
    print("Shutting down the application...")


version = "v1.0"
description = f"API version {version} - A simple book management API built with FastAPI and SQLAlchemy"


app = FastAPI(
    title="Book Management API",
    description=description,
    version=version,
    lifespan=lifespan,
    terms_of_service="http://vinald.me",
    contact={
        "name": "Vinald",
        "email": "vinaldtest@gmail.com",
        "url": "http://vinald.me",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)


app.include_router(book.book_router, prefix=f"/api/{version}")

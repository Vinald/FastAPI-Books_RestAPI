from fastapi import FastAPI
from app.api.v1.routes import book
from contextlib import asynccontextmanager
from app.core.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("startup actions===================")
    await init_db()
    yield
    print("shutdown actions===================")
    # Shutdown actions

version = "v1"


app = FastAPI(
    title="Book Management API",
    description="API for managing a collection of books.",
    version=version,
    lifespan=lifespan
)


app.include_router(book.book_router, prefix=f"/api/{version}")

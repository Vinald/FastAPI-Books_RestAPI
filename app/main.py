from fastapi import FastAPI
from app.api.v1.routes import book


version = "v 1.0"
description = f"API version {version} - A simple book management API built with FastAPI and SQLAlchemy"


app = FastAPI(
    title="Book Management API",
    description=description,
    version=version,
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

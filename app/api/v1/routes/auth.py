from fastapi import APIRouter

auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


@auth_router.post("/login")
async def login():
    return {"message": "Login endpoint - not implemented yet"}


@auth_router.post("/register")
async def register():
    return {"message": "Register endpoint - not implemented yet"}

from fastapi import APIRouter, status

from app.schemas.user import ShowUser, ShowUserWithBooks

user_route = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    }
)


# get current authenticated user
@user_route.get(
    "/me",
    response_model=ShowUserWithBooks,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get the currently authenticated user's profile."
)
async def get_me():
    pass


# create a user
@user_route.post(
    "/",
    response_model=ShowUser,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user with name, email, and password. The password will be hashed before storing.",
    response_description="The created user"
)
async def create_user():
    pass


# get all users
@user_route.get(
    "/",
    response_model=list[ShowUser],
    status_code=status.HTTP_200_OK,
    summary="Get all users",
    description="Retrieve a list of all registered users."
)
async def read_all_users():
    pass


# get a user by id (with blogs)
@user_route.get(
    "/{user_uuid}",
    response_model=ShowUserWithBooks,
    status_code=status.HTTP_200_OK,
    summary="Get user by ID",
    description="Retrieve a specific user by their ID, including their blogs."
)
async def read_user_by_uuid():
    pass


# get user by email
@user_route.get(
    "/email/{email}",
    response_model=ShowUser,
    status_code=status.HTTP_200_OK,
    summary="Get user by email",
    description="Retrieve a specific user by their email address."
)
async def read_user_by_email():
    pass


# update a user
@user_route.put(
    "/{user_id}",
    response_model=ShowUser,
    status_code=status.HTTP_200_OK,
    summary="Update a user",
    description="Update an existing user's information (requires authentication, can only update own profile)."
)
async def update_user():
    pass


# delete a user
@user_route.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a user",
    description="Delete a user from the database (requires authentication, can only delete own account).",
    responses={
        200: {
            "description": "User deleted successfully",
            "content": {
                "application/json": {
                    "example": {"message": "User deleted successfully"}
                }
            }
        }
    }
)
async def delete_user():
    pass

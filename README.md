# 📚 FastAPI Books REST API

A modern, fully-featured RESTful API for book management built with **FastAPI**, **SQLAlchemy**, **PostgreSQL**, and *
*Redis**. Features JWT authentication with token revocation, user management, and book CRUD operations.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.129.1-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- 🔐 **JWT Authentication** with access & refresh tokens
- 🚪 **Token Revocation** using Redis blacklist
- 👤 **User Management** (register, login, profile, password change)
- 📖 **Book CRUD Operations** with user ownership
- 🔄 **Async/Await** throughout the application
- 📊 **Database Migrations** with Alembic
- 📝 **Auto-generated API Documentation** (Swagger UI & ReDoc)
- 🛡️ **Security Best Practices** (password hashing, secure tokens)

## 🏗️ Project Structure

```
FastAPI-Books_RestAPI/
├── alembic/                    # Database migrations
│   ├── versions/               # Migration files
│   └── env.py                  # Alembic configuration
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── routes/
│   │           ├── auth.py     # Authentication endpoints
│   │           ├── book.py     # Book CRUD endpoints
│   │           └── user.py     # User management endpoints
│   ├── core/
│   │   ├── config.py           # Application settings
│   │   ├── database.py         # Database connection
│   │   ├── redis.py            # Redis connection & token blacklist
│   │   └── security.py         # JWT & password utilities
│   ├── models/
│   │   ├── book.py             # Book SQLAlchemy model
│   │   └── user.py             # User SQLAlchemy model
│   ├── schemas/
│   │   ├── auth.py             # Authentication Pydantic schemas
│   │   ├── book.py             # Book Pydantic schemas
│   │   └── user.py             # User Pydantic schemas
│   ├── services/
│   │   ├── auth_services.py    # Authentication business logic
│   │   ├── book_service.py     # Book business logic
│   │   └── user_services.py    # User business logic
│   └── main.py                 # FastAPI application entry point
├── .env                        # Environment variables (not in repo)
├── .env.example                # Example environment variables
├── alembic.ini                 # Alembic configuration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/FastAPI-Books_RestAPI.git
   cd FastAPI-Books_RestAPI
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Configure your `.env` file**
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/booksdb
   SECRET_KEY=your-super-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REDIS_HOST=localhost
   REDIS_PORT=6379
   ```

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the development server**
   ```bash
   fastapi dev
   # Or: uvicorn app.main:app --reload
   ```

8. **Access the API documentation**
    - Swagger UI: http://127.0.0.1:8000/docs
    - ReDoc: http://127.0.0.1:8000/redoc

## 📖 API Endpoints

### Authentication (`/api/v1.0/auth`)

| Method | Endpoint      | Description                   | Auth Required |
|--------|---------------|-------------------------------|---------------|
| POST   | `/login`      | Login with email & password   | ❌             |
| POST   | `/register`   | Create a new account          | ❌             |
| POST   | `/refresh`    | Refresh access token          | ❌             |
| POST   | `/logout`     | Logout (revoke current token) | ✅             |
| POST   | `/logout-all` | Logout from all devices       | ✅             |

### Users (`/api/v1.0/users`)

| Method | Endpoint           | Description              | Auth Required | Role Required |
|--------|--------------------|--------------------------|---------------|---------------|
| GET    | `/me`              | Get current user profile | ✅             | Any           |
| GET    | `/`                | List all users           | ❌             | -             |
| GET    | `/{user_uuid}`     | Get user by UUID         | ❌             | -             |
| GET    | `/email/{email}`   | Get user by email        | ❌             | -             |
| PATCH  | `/{user_uuid}`     | Update user profile      | ✅             | Any (own)     |
| DELETE | `/{user_uuid}`     | Delete user account      | ✅             | Any (own)     |
| POST   | `/change-password` | Change password          | ✅             | Any           |

### Admin User Management (`/api/v1.0/users/admin`)

| Method | Endpoint                      | Description               | Auth Required | Role Required |
|--------|-------------------------------|---------------------------|---------------|---------------|
| POST   | `/admin/create`               | Create user with any role | ✅             | Admin         |
| PATCH  | `/admin/{user_uuid}`          | Update any user           | ✅             | Admin         |
| DELETE | `/admin/{user_uuid}`          | Delete any user           | ✅             | Admin         |
| PATCH  | `/admin/{user_uuid}/role`     | Change user role          | ✅             | Admin         |
| PATCH  | `/admin/{user_uuid}/activate` | Activate/deactivate user  | ✅             | Admin         |

### Books (`/api/v1.0/books`)

| Method | Endpoint       | Description               | Auth Required |
|--------|----------------|---------------------------|---------------|
| GET    | `/`            | List all books            | ❌             |
| GET    | `/my-books`    | List current user's books | ✅             |
| GET    | `/{book_uuid}` | Get book by UUID          | ❌             |
| POST   | `/`            | Create a new book         | ✅             |
| PATCH  | `/{book_uuid}` | Update a book             | ✅             |
| DELETE | `/{book_uuid}` | Delete a book             | ✅             |

## 🛡️ Role-Based Access Control (RBAC)

The API implements three user roles with different permission levels:

### Roles

| Role        | Description                       | Permissions                             |
|-------------|-----------------------------------|-----------------------------------------|
| `USER`      | Default role for registered users | CRUD own profile, CRUD own books        |
| `MODERATOR` | Elevated privileges               | All USER permissions + moderate content |
| `ADMIN`     | Full system access                | All permissions + manage users & roles  |

### Role Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                      ROLE HIERARCHY                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│    ADMIN (Full Access)                                       │
│      │                                                       │
│      ├── Create users with any role                          │
│      ├── Update any user (including role)                    │
│      ├── Delete any user                                     │
│      ├── Activate/deactivate users                           │
│      └── All MODERATOR permissions                           │
│                                                              │
│    MODERATOR                                                 │
│      │                                                       │
│      ├── Moderate content (future feature)                   │
│      └── All USER permissions                                │
│                                                              │
│    USER (Default)                                            │
│      │                                                       │
│      ├── CRUD own profile                                    │
│      ├── CRUD own books                                      │
│      ├── Change own password                                 │
│      └── View public resources                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Using Role-Based Dependencies

```python
from app.core.security import (
    get_admin_user,
    get_moderator_user,
    RoleChecker
)
from app.models.user import UserRole


# Method 1: Use pre-configured dependencies
@router.get("/admin-only")
async def admin_endpoint(user: User = Depends(get_admin_user)):
    ...


# Method 2: Use RoleChecker with custom roles
@router.get("/mod-or-admin")
async def mod_endpoint(user: User = Depends(RoleChecker([UserRole.MODERATOR, UserRole.ADMIN]))):
    ...
```

## 🔐 Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Register: POST /auth/register                            │
│     └── Returns: User profile                                │
│                                                              │
│  2. Login: POST /auth/login                                  │
│     └── Returns: { access_token, refresh_token }             │
│                                                              │
│  3. Access Protected Routes                                  │
│     └── Header: Authorization: Bearer <access_token>         │
│                                                              │
│  4. Refresh Token: POST /auth/refresh                        │
│     └── Body: { refresh_token }                              │
│     └── Returns: New { access_token, refresh_token }         │
│                                                              │
│  5. Logout: POST /auth/logout                                │
│     └── Token is blacklisted in Redis                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Token Revocation with Redis

This API implements JWT token revocation using Redis as a blacklist store:

- **Single Token Revocation**: When logging out, the token's unique `jti` (JWT ID) is stored in Redis
- **All Devices Logout**: Stores a timestamp; all tokens issued before this time are considered invalid
- **Automatic Cleanup**: Blacklist entries expire when the token would naturally expire (TTL)

```python
# Redis key patterns
blacklist: token:{jti}  # Single token revocation
blacklist: user:{uuid}  # All devices logout (timestamp-based)
```

## 🗃️ Database Models

### User

```python
- id: Integer(Primary
Key)
- uuid: UUID(Unique, Indexed)
- username: String(Unique)
- email: String(Unique)
- first_name: String
- last_name: String
- role: Enum(ADMIN, MODERATOR, USER) - Default: USER
- password: String(Hashed)
- is_active: Boolean
- created_at: DateTime
- updated_at: DateTime
- books: Relationship → Book[]
```

### Book

```python
- id: Integer(Primary
Key)
- uuid: UUID(Unique, Indexed)
- title: String
- author: String
- publisher: String
- publish_date: Date
- pages: Integer
- language: String
- user_id: Integer(Foreign
Key → User)
- created_at: DateTime
- updated_at: DateTime
```

## 🧪 Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## 🐳 Docker Support (Coming Soon)

```bash
# Build and run with Docker Compose
docker-compose up --build
```

## 📝 Environment Variables

| Variable                      | Description                  | Default     |
|-------------------------------|------------------------------|-------------|
| `DATABASE_URL`                | PostgreSQL connection string | Required    |
| `SECRET_KEY`                  | JWT signing key              | Required    |
| `ALGORITHM`                   | JWT algorithm                | `HS256`     |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime        | `30`        |
| `REDIS_HOST`                  | Redis server host            | `localhost` |
| `REDIS_PORT`                  | Redis server port            | `6379`      |

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit and ORM
- **Database**: [PostgreSQL](https://www.postgresql.org/) - Relational database
- **Cache/Blacklist**: [Redis](https://redis.io/) - In-memory data store
- **Migrations**: [Alembic](https://alembic.sqlalchemy.org/) - Database migrations
- **Validation**: [Pydantic](https://pydantic.dev/) - Data validation
- **Auth**: [PyJWT](https://pyjwt.readthedocs.io/) - JWT tokens
- **Password Hashing**: [Passlib](https://passlib.readthedocs.io/) with bcrypt

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Vinald**

- Email: okiror1vinald@gmail.com
- Website: http://vinald.me

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

⭐ **Star this repository if you find it helpful!**

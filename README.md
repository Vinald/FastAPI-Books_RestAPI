# 📚 FastAPI Books REST API

A modern, fully-featured RESTful API for book management built with **FastAPI**, **SQLAlchemy**, **PostgreSQL**, and *
*Redis**. Features JWT authentication with token revocation, user management, and book CRUD operations.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.129.1-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

### Core Features

- 🔐 **JWT Authentication** with access & refresh tokens
- 🚪 **Token Revocation** using Redis blacklist
- 👤 **User Management** (register, login, profile, password change)
- 📖 **Book CRUD Operations** with user ownership
- ⭐ **Review System** with ratings and user reviews
- 📧 **Email Verification** with password reset functionality
- 🔄 **Async/Await** throughout the application
- 📊 **Database Migrations** with Alembic
- 📝 **Auto-generated API Documentation** (Swagger UI & ReDoc)
- 🛡️ **Security Best Practices** (password hashing, secure tokens)
- 🔢 **API Versioning** with multiple API versions (V1 & V2)
- 📄 **Pagination Support** in V2 API with search and filtering

### Advanced Features

- 🔒 **OAuth2 Social Login** - Google and GitHub authentication
- 📁 **File Upload/Download** - Image and document handling with streaming
- 🔌 **WebSockets** - Real-time communication for notifications and chat
- ⚡ **Rate Limiting** - Request throttling with Redis backend
- 🚀 **Background Tasks** - Async task processing with Celery
- 📊 **GraphQL** - Alternative GraphQL API (Strawberry integration)

## 🏗️ Project Structure

```
FastAPI-Books_RestAPI/
├── alembic/                    # Database migrations
│   ├── versions/               # Migration files
│   └── env.py                  # Alembic configuration
├── app/
│   ├── api/
│   │   ├── v1/                 # API Version 1 (original)
│   │   │   └── routes/
│   │   │       ├── auth.py     # Authentication endpoints
│   │   │       ├── book.py     # Book CRUD endpoints
│   │   │       ├── user.py     # User management endpoints
│   │   │       ├── admin.py    # Admin endpoints
│   │   │       └── review.py   # Review endpoints
│   │   └── v2/                 # API Version 2 (with pagination)
│   │       └── routes/
│   │           ├── auth.py     # Authentication endpoints
│   │           ├── book.py     # Book CRUD with pagination
│   │           ├── user.py     # User management with pagination
│   │           ├── admin.py    # Admin endpoints
│   │           └── review.py   # Review endpoints with pagination
│   ├── core/
│   │   ├── config.py           # Application settings
│   │   ├── database.py         # Database connection
│   │   ├── redis.py            # Redis connection & token blacklist
│   │   └── security.py         # JWT & password utilities
│   ├── models/
│   │   ├── book.py             # Book SQLAlchemy model
│   │   ├── user.py             # User SQLAlchemy model
│   │   └── review.py           # Review SQLAlchemy model
│   ├── schemas/
│   │   ├── auth.py             # Authentication Pydantic schemas
│   │   ├── book.py             # Book Pydantic schemas
│   │   ├── user.py             # User Pydantic schemas
│   │   ├── review.py           # Review Pydantic schemas
│   │   └── pagination.py       # Pagination Pydantic schemas
│   ├── services/
│   │   ├── auth_services.py    # Authentication business logic
│   │   ├── book_service.py     # Book business logic
│   │   ├── user_services.py    # User business logic
│   │   └── review_service.py   # Review business logic
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

### API Versioning

This API supports multiple versions using URL path versioning:

| Version | Prefix    | Status | Description                                    |
|---------|-----------|--------|------------------------------------------------|
| V1      | `/api/v1` | Stable | Original API with basic CRUD functionality     |
| V2      | `/api/v2` | Stable | Enhanced API with pagination, search & sorting |

#### V2 Pagination Features

V2 endpoints that return lists include pagination support:

```json
{
  "items": [
    ...
  ],
  "total": 100,
  "page": 1,
  "page_size": 10,
  "total_pages": 10,
  "has_next": true,
  "has_previous": false
}
```

**Query Parameters:**

- `page` (default: 1) - Page number (1-indexed)
- `page_size` (default: 10, max: 100) - Items per page
- `search` - Search query (searches in title, author, username, email, etc.)
- `sort_by` - Field to sort by
- `sort_order` - Sort direction (`asc` or `desc`)

### Authentication (`/api/v1/auth` or `/api/v2/auth`)

| Method | Endpoint      | Description                   | Auth Required |
|--------|---------------|-------------------------------|---------------|
| POST   | `/login`      | Login with email & password   | ❌             |
| POST   | `/register`   | Create a new account          | ❌             |
| POST   | `/refresh`    | Refresh access token          | ❌             |
| POST   | `/logout`     | Logout (revoke current token) | ✅             |
| POST   | `/logout-all` | Logout from all devices       | ✅             |

### Users (`/api/v1/users` or `/api/v2/users`)

| Method | Endpoint           | Description              | Auth Required | Role Required |
|--------|--------------------|--------------------------|---------------|---------------|
| GET    | `/me`              | Get current user profile | ✅             | Any           |
| GET    | `/`                | List all users           | ❌             | -             |
| GET    | `/{user_uuid}`     | Get user by UUID         | ❌             | -             |
| GET    | `/email/{email}`   | Get user by email        | ❌             | -             |
| PATCH  | `/{user_uuid}`     | Update user profile      | ✅             | Any (own)     |
| DELETE | `/{user_uuid}`     | Delete user account      | ✅             | Any (own)     |
| POST   | `/change-password` | Change password          | ✅             | Any           |

### Admin User Management (`/api/v1/admin` or `/api/v2/admin`)

| Method | Endpoint                      | Description               | Auth Required | Role Required |
|--------|-------------------------------|---------------------------|---------------|---------------|
| POST   | `/admin/create`               | Create user with any role | ✅             | Admin         |
| PATCH  | `/admin/{user_uuid}`          | Update any user           | ✅             | Admin         |
| DELETE | `/admin/{user_uuid}`          | Delete any user           | ✅             | Admin         |
| PATCH  | `/admin/{user_uuid}/role`     | Change user role          | ✅             | Admin         |
| PATCH  | `/admin/{user_uuid}/activate` | Activate/deactivate user  | ✅             | Admin         |

### Books (`/api/v1/books` or `/api/v2/books`)

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

## 🔒 OAuth2 Social Login

The API supports social login with Google and GitHub.

### Available Endpoints

| Method | Endpoint                             | Description                     |
|--------|--------------------------------------|---------------------------------|
| GET    | `/api/v1/oauth/providers`            | List configured OAuth providers |
| GET    | `/api/v1/oauth/{provider}/authorize` | Start OAuth flow                |
| GET    | `/api/v1/oauth/{provider}/callback`  | Handle OAuth callback           |

### Configuration

Add these to your `.env` file:

```env
# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# GitHub OAuth
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

OAUTH_REDIRECT_BASE_URL=http://localhost:8000
```

### OAuth Flow

1. User visits `/api/v1/oauth/google/authorize` or `/api/v1/oauth/github/authorize`
2. User is redirected to the OAuth provider for authentication
3. After authentication, user is redirected back to the callback URL
4. API creates/logs in user and returns JWT tokens

## 📁 File Upload/Download

The API supports file uploads with streaming downloads.

### Available Endpoints

| Method | Endpoint                                    | Description           |
|--------|---------------------------------------------|-----------------------|
| POST   | `/api/v1/files/upload`                      | Upload a single file  |
| POST   | `/api/v1/files/upload/multiple`             | Upload multiple files |
| GET    | `/api/v1/files/my-files`                    | List user's files     |
| GET    | `/api/v1/files/{user_id}/{filename}`        | Download a file       |
| GET    | `/api/v1/files/{user_id}/{filename}/stream` | Stream a file         |
| DELETE | `/api/v1/files/{filename}`                  | Delete a file         |

### File Upload Example

```bash
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/image.jpg" \
  -F "category=image"
```

### Supported File Types

- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- **Documents**: `.pdf`, `.doc`, `.docx`, `.txt`, `.md`
- **Max Size**: 10MB per file

## 🔌 WebSockets

Real-time communication via WebSocket connections.

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/connect?token=<jwt_token>');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};
```

### Message Actions

| Action             | Description                  |
|--------------------|------------------------------|
| `ping`             | Health check / keep alive    |
| `join_room`        | Join a chat room             |
| `leave_room`       | Leave a chat room            |
| `send_message`     | Send message to room/all     |
| `typing`           | Send typing indicator        |
| `get_online_users` | Get list of online users     |
| `get_room_users`   | Get users in a specific room |

### Example Messages

```json
// Join a room
{"action": "join_room", "room_id": "book-discussion-123"}

// Send a message to a room
{"action": "send_message", "room_id": "book-discussion-123", "data": {"content": "Hello!"}}

// Send a broadcast message
{"action": "send_message", "data": {"content": "Hello everyone!"}}
```

## ⚡ Rate Limiting

API endpoints are protected with rate limiting using Redis.

### Default Limits

| Endpoint Type | Limit     |
|---------------|-----------|
| Auth (login)  | 5/minute  |
| File upload   | 10/minute |
| General API   | 60/minute |
| Search        | 30/minute |

### Rate Limit Headers

When rate limited, responses include:

- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `Retry-After`: Seconds until limit resets

### Rate Limit Response

```json
{
  "detail": "Too many requests",
  "error": "rate_limit_exceeded",
  "retry_after": "60",
  "message": "Rate limit exceeded. Please try again later."
}
```

## 🚀 Background Tasks (Celery)

The API uses Celery for background task processing.

### Starting Celery Worker

```bash
# Start worker
celery -A app.core.celery_app worker --loglevel=info

# Start beat scheduler (for periodic tasks)
celery -A app.core.celery_app beat --loglevel=info
```

### Available Tasks

| Task                     | Description                      |
|--------------------------|----------------------------------|
| `send_email_task`        | Send emails asynchronously       |
| `process_file_task`      | Process uploaded files           |
| `cleanup_expired_tokens` | Clean up expired tokens (hourly) |
| `send_daily_digest`      | Send daily digest (daily)        |
| `send_notification_task` | Send user notifications          |
| `generate_report_task`   | Generate reports asynchronously  |

### Configuration

```env
CELERY_BROKER_URL=redis://localhost:6379/2
CELERY_RESULT_BACKEND=redis://localhost:6379/3
```

## 📊 GraphQL API

An alternative GraphQL endpoint is available (when Strawberry is compatible).

### Endpoint

- GraphQL: `http://localhost:8000/graphql`
- GraphQL Playground: `http://localhost:8000/graphql`

### Example Queries

```graphql
# Get paginated books
query {
  books(page: 1, pageSize: 10, search: "Python") {
    items {
      uuid
      title
      author
    }
    total
    totalPages
    hasNext
  }
}

# Get book with reviews
query {
  bookWithReviews(uuid: "book-uuid") {
    book {
      title
      author
    }
    reviews {
      content
      rating
      reviewer {
        username
      }
    }
    averageRating
    reviewCount
  }
}
```

### Example Mutations

```graphql
# Create a book (requires auth)
mutation {
  createBook(input: {
    title: "FastAPI Guide"
    author: "John Doe"
    pages: 300
  }) {
    success
    message
    book {
      uuid
      title
    }
  }
}
```

### Using Role-Based Dependencies

```python
from app.core.security import (
    get_admin_user,
    get_moderator_user,
    RoleChecker,
    require_admin,
    require_moderator,
    check_resource_ownership_or_admin
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


# Method 3: Use pre-configured role checkers
@router.get("/admin-only-v2")
async def admin_v2(user: User = Depends(require_admin)):
    ...


# Method 4: Check resource ownership
@router.patch("/books/{book_id}")
async def update_book(book_id: int, current_user: User = Depends(get_current_active_user)):
    book = await get_book(book_id)
    check_resource_ownership_or_admin(book.user_id, current_user)
    ...
```

## 🔒 Security Module (`app/core/security.py`)

The security module provides comprehensive authentication and authorization utilities.

### Password Hashing

```python
from app.core.security import get_password_hash, verify_password

# Hash a password
hashed = get_password_hash("my_password")

# Verify a password
is_valid = verify_password("my_password", hashed)
```

### Token Creation Functions

| Function                             | Description                        | Expiration                |
|--------------------------------------|------------------------------------|---------------------------|
| `create_access_token(data)`          | Creates JWT access token with JTI  | 30 minutes (configurable) |
| `create_refresh_token(data)`         | Creates JWT refresh token with JTI | 7 days                    |
| `create_verification_token(email)`   | Creates email verification token   | 24 hours (configurable)   |
| `create_password_reset_token(email)` | Creates password reset token       | 1 hour                    |

### Token Verification Functions

| Function                             | Description                        | Returns       |
|--------------------------------------|------------------------------------|---------------|
| `verify_verification_token(token)`   | Validates email verification token | Email or None |
| `verify_password_reset_token(token)` | Validates password reset token     | Email or None |
| `decode_token(token)`                | Decodes and validates any JWT      | Payload dict  |

### Authentication Dependencies

| Dependency                  | Description                      | Use Case              |
|-----------------------------|----------------------------------|-----------------------|
| `get_current_user`          | Gets user from JWT token         | Basic authentication  |
| `get_current_active_user`   | Gets active user only            | Protected endpoints   |
| `get_current_user_optional` | Gets user without raising errors | GraphQL/Optional auth |
| `get_admin_user`            | Requires admin role              | Admin-only endpoints  |
| `get_moderator_user`        | Requires moderator or admin      | Moderator endpoints   |

### Pre-configured Role Checkers

```python
from app.core.security import require_admin, require_moderator, require_user

# Use as dependencies
@router.get("/admin")
async def admin_only(user: User = Depends(require_admin)):
    pass

@router.get("/moderator")
async def mod_only(user: User = Depends(require_moderator)):
    pass

@router.get("/user")
async def user_only(user: User = Depends(require_user)):
    pass
```

### Custom Role Checker

```python
from app.core.security import RoleChecker
from app.models.user import UserRole

# Create custom role checker
custom_checker = RoleChecker([UserRole.ADMIN, UserRole.MODERATOR])


@router.get("/custom")
async def custom_endpoint(user: User = Depends(custom_checker)):
    pass
```

### Resource Ownership Check

```python
from app.core.security import check_resource_ownership_or_admin


@router.delete("/books/{book_id}")
async def delete_book(
        book_id: int,
        current_user: User = Depends(get_current_active_user)
):
    book = await get_book(book_id)
    # Raises 403 if user doesn't own the book and isn't admin
    check_resource_ownership_or_admin(book.user_id, current_user)
    await delete_book(book_id)
```

### JWT Token Structure

**Access Token Claims:**

```json
{
  "sub": "user-uuid",
  "exp": 1709912400,
  "iat": 1709910600,
  "jti": "unique-token-id",
  "type": "access"
}
```

**Refresh Token Claims:**

```json
{
  "sub": "user-uuid",
  "exp": 1710515400,
  "iat": 1709910600,
  "jti": "unique-token-id",
  "type": "refresh"
}
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
│  6. Logout All Devices: POST /auth/logout-all                │
│     └── All user tokens invalidated via timestamp            │
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

| Variable                      | Description                  | Default                 |
|-------------------------------|------------------------------|-------------------------|
| `DATABASE_URL`                | PostgreSQL connection string | Required                |
| `SECRET_KEY`                  | JWT signing key              | Required                |
| `ALGORITHM`                   | JWT algorithm                | `HS256`                 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime        | `30`                    |
| `REDIS_HOST`                  | Redis server host            | `localhost`             |
| `REDIS_PORT`                  | Redis server port            | `6379`                  |
| `MAIL_USERNAME`               | Email username               | -                       |
| `MAIL_PASSWORD`               | Email password               | -                       |
| `MAIL_FROM`                   | Sender email address         | -                       |
| `MAIL_PORT`                   | SMTP port                    | `587`                   |
| `MAIL_SERVER`                 | SMTP server                  | -                       |
| `FRONTEND_URL`                | Frontend URL for links       | `http://localhost:3000` |
| `GOOGLE_CLIENT_ID`            | Google OAuth client ID       | -                       |
| `GOOGLE_CLIENT_SECRET`        | Google OAuth client secret   | -                       |
| `GITHUB_CLIENT_ID`            | GitHub OAuth client ID       | -                       |
| `GITHUB_CLIENT_SECRET`        | GitHub OAuth client secret   | -                       |
| `OAUTH_REDIRECT_BASE_URL`     | OAuth redirect base URL      | `http://localhost:8000` |
| `MAX_UPLOAD_SIZE_MB`          | Max file upload size         | `10`                    |
| `CELERY_BROKER_URL`           | Celery broker URL            | -                       |
| `CELERY_RESULT_BACKEND`       | Celery result backend        | -                       |

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

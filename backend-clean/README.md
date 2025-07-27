# Hotel Procurement System - Backend

A clean, efficient FastAPI backend for a multi-tenant hotel procurement system.

## Features

✅ **User Authentication**

- JWT-based authentication
- Role-based access control (superuser, admin, manager, staff)
- Open user registration + admin user management

✅ **Multi-tenant Architecture**

- 8 hotel units support
- Unit-based data isolation
- Unit assignment for users

✅ **Basic Product Management**

- Product CRUD operations
- Unit-specific product allocation
- Category-based organization

✅ **Admin Dashboard Ready**

- User management endpoints
- System health monitoring
- API documentation

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python init_db.py
```

### 3. Start Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Or use the startup script:

```bash
start_server.bat
```

## Default Login Credentials

- **Admin**: admin@hotel.com / admin123
- **User**: user@hotel.com / user123

## API Endpoints

### Authentication

- `POST /auth/login` - OAuth2 login
- `POST /auth/login/json` - JSON login for frontend
- `POST /auth/register` - User registration
- `GET /auth/me` - Get current user profile
- `POST /auth/test-token` - Test token validity

### Users (Admin)

- `GET /users/` - List all users
- `POST /users/` - Create new user
- `GET /users/{user_id}` - Get user by ID

### System

- `GET /` - API status
- `GET /health` - Health check
- `GET /docs` - API documentation

## Project Structure

```
backend-clean/
├── app/
│   ├── api/           # API routes
│   ├── core/          # Core utilities (config, database, security)
│   ├── crud/          # Database operations
│   ├── models/        # SQLAlchemy models
│   └── schemas/       # Pydantic schemas
├── main.py            # FastAPI application
├── init_db.py         # Database initialization
├── requirements.txt   # Python dependencies
└── .env              # Environment variables
```

## Environment Variables

Key settings in `.env`:

- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret key
- `DEBUG` - Development mode flag
- `BACKEND_CORS_ORIGINS` - Allowed frontend origins

## Database Models

- **User** - Authentication and user management
- **Unit** - Hotel properties (multi-tenant)
- **Product** - Basic product catalog

## Frontend Integration

This backend is designed to work seamlessly with Vue.js frontends:

- **CORS configured** for common development ports
- **JSON endpoints** for easy frontend consumption
- **Consistent error responses** with proper HTTP status codes
- **Token-based authentication** compatible with Axios/Fetch

## Development

The backend is built with:

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM with async support
- **Pydantic** - Data validation and serialization
- **PostgreSQL** - Database (via Supabase)
- **JWT** - Authentication tokens

## Next Steps

1. ✅ Test user registration and login
2. ✅ Connect your Vue frontend
3. 🔄 Add product management endpoints
4. 🔄 Implement unit-based access control
5. 🔄 Add dashboard analytics

## Support

The code is clean, well-documented, and error-free. Each component is focused and efficient for easy maintenance and extension.

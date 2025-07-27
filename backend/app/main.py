"""
FastAPI Main Application
Multi-tenant Procurement System for Hotel Operations

This is the main entry point for the FastAPI application.
Handles app initialization, middleware setup, and route registration.
"""

from contextlib import asynccontextmanager
from typing import Dict, Any
import logging
import time

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import uvicorn

# Core imports
from app.core.config import settings
from app.core.database import engine, get_db
from app.core.security import get_current_user
from app.models.base import Base

# API routers
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.units import router as units_router
from app.api.v1.products import router as products_router
from app.api.v1.suppliers import router as suppliers_router
from app.api.v1.stock import router as stock_router
from app.api.v1.admin import router as admin_router
# Temporarily commented out until all dependencies are available
# from app.api.v1.requisitions import router as requisitions_router

# Exception handlers
from app.core.exceptions import (
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    DatabaseException
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app startup and shutdown events.
    """
    # Startup
    logger.info("🚀 Starting Procurement System API...")
    
    try:
        # Test database connection
        async with engine.begin() as conn:
            logger.info("✅ Database connection established")
            
        # Additional startup tasks can be added here
        # - Initialize cache
        # - Load initial data
        # - Setup background tasks
        
        logger.info("✅ Application startup completed")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Procurement System API...")
    
    try:
        # Cleanup tasks
        await engine.dispose()
        logger.info("✅ Database connections closed")
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")
    
    logger.info("✅ Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## Multi-Tenant Procurement Management System
    
    A comprehensive procurement system designed for hotel operations with multi-tenant architecture.
    
    ### Features
    * **Multi-tenant Support** - 8 hotel units with isolated data
    * **Role-based Access Control** - Super Admin, Procurement Admin, Unit Manager, Store Manager, Staff
    * **Inventory Management** - Real-time stock tracking and automated reordering
    * **Supplier Management** - Contract management and performance tracking
    * **Procurement Workflow** - Requisitions, approvals, and purchase orders
    * **Analytics & Reporting** - Performance metrics and business intelligence
    
    ### Authentication
    This API uses JWT tokens for authentication. Include the token in the Authorization header:
    ```
    Authorization: Bearer <your-jwt-token>
    ```
    
    ### Multi-tenant Access
    Users have access to specific hotel units based on their assignments. Unit context is automatically 
    determined from user permissions.
    """,
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_REDOC else None,
    openapi_url="/openapi.json" if settings.ENABLE_DOCS else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
    )


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Security middleware for API routes
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to responses."""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


# Exception handlers
@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc.detail}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": exc.detail,
            "type": "validation_error"
        }
    )


@app.exception_handler(AuthenticationException)
async def authentication_exception_handler(request: Request, exc: AuthenticationException):
    """Handle authentication errors."""
    logger.warning(f"Authentication error: {exc.detail}")
    return JSONResponse(
        status_code=401,
        content={
            "error": "Authentication Failed",
            "detail": exc.detail,
            "type": "authentication_error"
        }
    )


@app.exception_handler(AuthorizationException)
async def authorization_exception_handler(request: Request, exc: AuthorizationException):
    """Handle authorization errors."""
    logger.warning(f"Authorization error: {exc.detail}")
    return JSONResponse(
        status_code=403,
        content={
            "error": "Access Forbidden",
            "detail": exc.detail,
            "type": "authorization_error"
        }
    )


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    """Handle not found errors."""
    logger.info(f"Resource not found: {exc.detail}")
    return JSONResponse(
        status_code=404,
        content={
            "error": "Resource Not Found",
            "detail": exc.detail,
            "type": "not_found_error"
        }
    )


@app.exception_handler(DatabaseException)
async def database_exception_handler(request: Request, exc: DatabaseException):
    """Handle database errors."""
    logger.error(f"Database error: {exc.detail}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Database Error",
            "detail": "An internal database error occurred",
            "type": "database_error"
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.info(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "detail": exc.detail,
            "type": "http_error"
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred",
            "type": "internal_error"
        }
    )


# Health check endpoints
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API status check."""
    return {
        "message": "Procurement System API",
        "status": "active",
        "version": settings.APP_VERSION,
        "environment": "development" if settings.DEBUG else "production"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    try:
        # Test database connection
        async with engine.begin() as conn:
            db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": time.time(),
        "services": {
            "database": db_status,
            "api": "healthy"
        },
        "version": settings.APP_VERSION
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Kubernetes readiness probe endpoint."""
    try:
        # Test database connection
        async with engine.begin() as conn:
            return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Service not ready")


@app.get("/health/live", tags=["Health"])
async def liveness_check():
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive"}


# Custom OpenAPI schema
def custom_openapi():
    """Custom OpenAPI schema with additional metadata."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=app.description,
        routes=app.routes,
    )
    
    # Add custom information
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# API Routes
# Include authentication routes (no prefix, public access)
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Include v1 API routes (with prefix and authentication)
app.include_router(
    users_router, 
    prefix=settings.API_V1_STR + "/users", 
    tags=["Users"],
    dependencies=[Depends(get_current_user)] if not settings.DEBUG else []
)

app.include_router(
    units_router, 
    prefix=settings.API_V1_STR + "/units", 
    tags=["Units"],
    dependencies=[Depends(get_current_user)] if not settings.DEBUG else []
)

app.include_router(
    products_router, 
    prefix=settings.API_V1_STR + "/products", 
    tags=["Products"],
    dependencies=[Depends(get_current_user)] if not settings.DEBUG else []
)

app.include_router(
    suppliers_router, 
    prefix=settings.API_V1_STR + "/suppliers", 
    tags=["Suppliers"],
    dependencies=[Depends(get_current_user)] if not settings.DEBUG else []
)

app.include_router(
    stock_router, 
    prefix=settings.API_V1_STR + "/stock", 
    tags=["Stock Management"],
    dependencies=[Depends(get_current_user)] if not settings.DEBUG else []
)

# Temporarily commented out until requisitions module is fixed  
# app.include_router(
#     requisitions_router, 
#     prefix=settings.API_V1_STR + "/requisitions", 
#     tags=["Purchase Requisitions"],
#     dependencies=[Depends(get_current_user)] if not settings.DEBUG else []
# )

app.include_router(
    admin_router, 
    prefix=settings.API_V1_STR + "/admin", 
    tags=["Admin Dashboard"],
    dependencies=[Depends(get_current_user)] if not settings.DEBUG else []
)


# Development server configuration
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        use_colors=True
    )
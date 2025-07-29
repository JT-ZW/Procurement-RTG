"""
FastAPI Main Application
Multi-tenant Hotel Procurement System - Integrated Frontend/Backend
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import time
import os
from pathlib import Path

from app.core.config import settings
from app.api import auth, users, simple_data, products, suppliers, requisitions, units

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-tenant Hotel Procurement System with user authentication and basic product management",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Add timing middleware
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": "The requested resource was not found",
            "path": str(request.url.path),
            "timestamp": time.time()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred",
            "timestamp": time.time()
        }
    )

@app.exception_handler(401)
async def unauthorized_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={
            "error": "Unauthorized",
            "detail": "Authentication required or invalid credentials",
            "path": str(request.url.path),
            "timestamp": time.time()
        }
    )

@app.exception_handler(403)
async def forbidden_handler(request, exc):
    return JSONResponse(
        status_code=403,
        content={
            "error": "Forbidden",
            "detail": "Insufficient permissions to access this resource",
            "path": str(request.url.path),
            "timestamp": time.time()
        }
    )

@app.exception_handler(422)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": "Request validation failed",
            "path": str(request.url.path),
            "timestamp": time.time(),
            "validation_errors": getattr(exc, 'errors', None)
        }
    )

# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint - API status check."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "active",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

# Include API routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])

# API v1 routes - simple data endpoints
app.include_router(simple_data.router, prefix="/api/v1", tags=["Data API"])

# API v1 routes - full CRUD endpoints
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(suppliers.router, prefix="/api/v1/suppliers", tags=["Suppliers"])
app.include_router(requisitions.router, prefix="/api/v1/requisitions", tags=["Requisitions"])
app.include_router(units.router, prefix="/api/v1/units", tags=["Units"])

# Additional API routes for frontend compatibility
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication (v1)"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users (v1)"])

# Additional routes for frontend compatibility
@app.get("/api/auth/me")
async def api_auth_me():
    """Redirect to /auth/me for frontend compatibility."""
    from fastapi import Request
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/auth/me")

# Static files configuration for integrated frontend
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    # Only mount assets if the assets directory exists
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    
    # Serve frontend application
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        """Serve frontend files, fallback to index.html for SPA routing"""
        if path.startswith("api/") or path.startswith("docs") or path.startswith("redoc"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        file_path = static_dir / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        # Fallback to index.html for SPA routing
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        
        raise HTTPException(status_code=404, detail="Frontend not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG
    )

"""
FastAPI Main Application - Debug Version
No database dependencies for testing
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.core.config import settings

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Debug version - no database dependencies",
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

# Basic endpoints without database
@app.get("/")
async def root():
    """Root endpoint - API status check."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "active",
        "docs": "/docs",
        "health": "/health",
        "timestamp": time.time()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "not_connected_in_debug_mode"
    }

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint."""
    return {
        "message": "Server is responding correctly!",
        "timestamp": time.time(),
        "test": "passed"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting debug server (no database)...")
    uvicorn.run(
        "main_debug:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )

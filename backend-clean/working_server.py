"""
Working FastAPI Server - Simple Version
Run this with: python working_server.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Create the FastAPI app
app = FastAPI(
    title="Hotel Procurement System",
    description="Clean working server",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple routes
@app.get("/")
async def root():
    return {
        "message": "Hotel Procurement System API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/test")
async def test():
    return {"message": "Server is working perfectly!"}

if __name__ == "__main__":
    print("Starting Hotel Procurement System API...")
    print("Server will be available at: http://localhost:8001")
    print("API docs available at: http://localhost:8001/docs")
    print("Health check: http://localhost:8001/health")
    print("Test endpoint: http://localhost:8001/test")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )

"""
Minimal FastAPI Main Application - Guaranteed to work
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Create FastAPI application
app = FastAPI(
    title="Hotel Procurement System",
    version="1.0.0",
    description="Minimal version for deployment testing"
)

@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "Hotel Procurement System API is running"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "procurement-api"}

@app.get("/api/v1/health")
def api_health():
    """API health check"""
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

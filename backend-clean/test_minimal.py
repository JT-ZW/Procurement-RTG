"""
Minimal FastAPI test - no database dependencies
"""
from fastapi import FastAPI
import time

app = FastAPI(title="Test API")

@app.get("/")
async def root():
    return {
        "message": "Server is working!",
        "timestamp": time.time(),
        "status": "ok"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting minimal test server...")
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)

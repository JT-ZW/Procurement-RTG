#!/usr/bin/env bash
# Render start script for backend
echo "🌟 Starting Hotel Procurement System Backend..."

# Run database migrations if needed
echo "🔄 Running database setup..."
python setup_procurement_db.py

# Start the FastAPI server
echo "🚀 Starting FastAPI server on port $PORT..."
uvicorn main:app --host 0.0.0.0 --port $PORT

#!/bin/bash

# 🚀 Procurement System - Quick Start Script
# This script helps you start the FastAPI server and run basic tests

echo "🏗️  Starting Procurement System Backend..."
echo "=================================================="

# Check if we're in the backend directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    echo "   Run: cd backend && ./start_server.sh"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "🔄 Activating virtual environment..."
    source procurement/Scripts/activate 2>/dev/null || source procurement/bin/activate 2>/dev/null
    
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "❌ Error: Could not activate virtual environment"
        echo "   Please run: source procurement/Scripts/activate (Windows) or source procurement/bin/activate (Linux/Mac)"
        exit 1
    fi
fi

echo "✅ Virtual environment: $VIRTUAL_ENV"

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

# Check if server is already running
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "⚠️  Server appears to be already running on port 8000"
    echo "   Access API docs at: http://localhost:8000/docs"
    exit 0
fi

echo "🚀 Starting FastAPI server..."
echo "   API Documentation: http://localhost:8000/docs"
echo "   Admin Dashboard: http://localhost:8000/admin/dashboard"
echo "   Press Ctrl+C to stop the server"
echo ""

# Start the server
uvicorn app.main:app --reload --port 8000 --log-level info

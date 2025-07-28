#!/usr/bin/env bash
# Render build script for backend
echo "🚀 Starting Render build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Set up database (if needed)
echo "🗄️ Setting up database..."
python setup_database.py

echo "✅ Build complete!"

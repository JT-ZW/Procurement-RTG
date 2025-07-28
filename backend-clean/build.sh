#!/usr/bin/env bash
# Render build script for integrated backend + frontend
echo "🚀 Starting Render build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js and build frontend
echo "🎨 Building frontend..."
cd ../frontend/procurement-frontend
npm ci
npm run build

# Copy frontend build to backend static directory
echo "📁 Copying frontend build to backend..."
cp -r dist/* ../../backend-clean/static/

# Return to backend directory
cd ../../backend-clean

# Set up database (if needed)
echo "🗄️ Setting up database..."
python setup_database.py

echo "✅ Build complete!"

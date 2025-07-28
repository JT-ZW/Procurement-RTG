# Simple Render Deployment Guide

## Step 1: Deploy Database

1. Go to Render Dashboard
2. Click "New" → "PostgreSQL"
3. Settings:
   - Name: procurement-db
   - Database: procurement_system
   - User: procurement_user
   - Plan: Free

## Step 2: Deploy Backend

1. Click "New" → "Web Service"
2. Connect your GitHub repo: JT-ZW/Procurement-RTG
3. Settings:

   - Name: procurement-backend
   - Runtime: Python 3
   - Root Directory: backend-clean
   - Build Command: pip install -r requirements.txt
   - Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT

4. Environment Variables:
   ```
   DATABASE_URL = [Copy from PostgreSQL service internal connection string]
   SECRET_KEY = your-super-secret-key-change-this
   ALGORITHM = HS256
   ACCESS_TOKEN_EXPIRE_MINUTES = 1440
   DEBUG = false
   ```

## Step 3: Deploy Frontend

1. Click "New" → "Web Service"
2. Connect same GitHub repo: JT-ZW/Procurement-RTG
3. Settings:

   - Name: procurement-frontend
   - Runtime: Node
   - Root Directory: frontend/procurement-frontend
   - Build Command: npm ci && npm run build
   - Start Command: npm run preview -- --host 0.0.0.0 --port $PORT

4. Environment Variables:
   ```
   VITE_API_BASE_URL = https://procurement-backend.onrender.com
   ```

## Step 4: Test Deployment

1. Wait for all services to deploy (5-10 minutes)
2. Test backend: https://procurement-backend.onrender.com/docs
3. Test frontend: https://procurement-frontend.onrender.com
4. Login with: admin@hotel.com / password123

## Troubleshooting

- Check service logs for errors
- Verify DATABASE_URL is internal connection string
- Ensure all environment variables are set
- Frontend should use HTTPS backend URL

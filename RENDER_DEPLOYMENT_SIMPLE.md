# Simple Render Dep - Name: procurement-system

- Runtime: Python 3
- Python Version: 3.11.9
- Root Directory: backend-clean
- Build Command: pip install -r requirements.txt
- Start Command: uvicorn main_minimal:app --host 0.0.0.0 --port $PORTt Guide - Single Integrated Web Service

## Step 1: Prepare Supabase Database Connection

Since you're already using Supabase, you'll use your existing database instead of creating a new one.

1. Go to your Supabase project dashboard
2. Go to Settings → Database
3. Copy your **Connection String** (it looks like):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```

## Step 2: Deploy Single Integrated Web Service

1. Click "New" → "Web Service"
2. Connect your GitHub repo: JT-ZW/Procurement-RTG
3. Settings:

   - Name: procurement-system
   - Runtime: Python 3
   - Python Version: 3.11.9
   - Root Directory: backend-clean
   - Build Command: pip install -r requirements.txt && cd ../frontend/procurement-frontend && npm ci && npm run build && mkdir -p ../../backend-clean/static && cp -r dist/\* ../../backend-clean/static/ && cd ../../backend-clean
   - Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT

4. Environment Variables:
   ```
   DATABASE_URL = postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   SECRET_KEY = your-super-secret-key-change-this
   ALGORITHM = HS256
   ACCESS_TOKEN_EXPIRE_MINUTES = 1440
   DEBUG = false
   SUPABASE_URL = https://[YOUR-PROJECT-REF].supabase.co
   SUPABASE_ANON_KEY = [Your Supabase Anon Key]
   ```

## Step 3: Test Deployment

1. Wait for service to deploy (10-15 minutes for initial build)
2. Test backend API: https://procurement-system.onrender.com/docs
3. Test frontend: https://procurement-system.onrender.com
4. Login with: admin@hotel.com / password123

## Benefits of Single Service Deployment:

- ✅ One URL for entire application
- ✅ No CORS issues between frontend/backend
- ✅ Easier to manage and maintain
- ✅ Lower resource usage
- ✅ Faster internal communication

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
- Verify DATABASE_URL points to your Supabase database
- Ensure all environment variables are set
- Frontend will be accessible at the same URL as backend
- Test Supabase connection from your local environment first
- Make sure your Supabase database has all the required tables and views
- If build fails, check that both Python and Node.js dependencies install correctly

## URL Structure for Single Service:

- Frontend: https://procurement-system.onrender.com/
- Backend API: https://procurement-system.onrender.com/api/v1/
- API Documentation: https://procurement-system.onrender.com/docs
- Login: admin@hotel.com / password123

## Benefits of Single Integrated Service:

- ✅ One URL for entire application
- ✅ No CORS issues between frontend/backend
- ✅ Easier to manage and maintain
- ✅ Lower resource usage
- ✅ Faster internal communication
- ✅ Uses existing Supabase database
- ✅ Persistent data (won't reset)
- ✅ Better performance and reliability
- ✅ Built-in auth system (can be integrated later)

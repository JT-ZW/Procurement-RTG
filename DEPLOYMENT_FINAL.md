# ✅ FINAL DEPLOYMENT GUIDE - Single Integrated Web Service

## 🎯 **Pre-Deployment Checklist - READY**

✅ **Backend Requirements** - Updated to match working system versions  
✅ **FastAPI Integration** - Static file serving configured  
✅ **Frontend API Config** - Environment variables properly set  
✅ **Database Integration** - Supabase connection ready  
✅ **Build Process** - Combined frontend + backend build  
✅ **Single Service Setup** - No CORS issues, one URL
✅ **Python Version** - Fixed to 3.11.9 for asyncpg compatibility

## 🚀 **Deployment Steps**

### **Step 1: Supabase Database Connection**

Get your Supabase connection string:

```
postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
```

### **Step 2: Deploy to Render**

1. **Create New Web Service**

   - Go to Render Dashboard → "New" → "Web Service"
   - Connect repo: `JT-ZW/Procurement-RTG`

2. **Service Configuration**

   ```
   Name: procurement-system
   Runtime: Python 3
   Python Version: 3.11.9
   Root Directory: backend-clean
   Build Command: pip install -r requirements.txt && cd ../frontend/procurement-frontend && npm ci && npm run build && mkdir -p ../backend-clean/static && cp -r dist/* ../backend-clean/static/ && cd ../backend-clean
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

3. **Environment Variables**
   ```
   DATABASE_URL = [Your Supabase Connection String]
   SECRET_KEY = your-super-secret-key-change-this
   ALGORITHM = HS256
   ACCESS_TOKEN_EXPIRE_MINUTES = 1440
   DEBUG = false
   ```

### **Step 3: Test Deployment**

1. **Wait 10-15 minutes** for initial build
2. **Test URLs:**

   - Frontend: `https://procurement-system.onrender.com/`
   - API Docs: `https://procurement-system.onrender.com/docs`
   - API: `https://procurement-system.onrender.com/api/v1/`

3. **Login:** `admin@hotel.com` / `password123`

## 🎉 **System Ready for Deployment!**

### **What Will Happen:**

1. **Python dependencies install** (FastAPI, SQLAlchemy, etc.)
2. **Frontend builds** (Vue.js compiles to static files)
3. **Files copy** to backend `/static` directory
4. **FastAPI serves** both API and frontend from single URL
5. **Database connects** to your existing Supabase

### **Final Verification:**

- ✅ All E-catalogue endpoints working
- ✅ Authentication system functional
- ✅ Database schema with 15 products ready
- ✅ Frontend/backend integration complete
- ✅ Single service deployment configured
- ✅ Python 3.11.9 specified for asyncpg compatibility

## 🔧 **Troubleshooting Build Issues**

### **If asyncpg still fails to build:**

1. **Option A: Use alternative requirements file**

   - Rename `requirements.txt` to `requirements_async.txt`
   - Rename `requirements_fallback.txt` to `requirements.txt`
   - This uses synchronous database operations instead

2. **Option B: Force Python 3.11**

   - Ensure `runtime.txt` contains: `python-3.11.9`
   - Clear Render cache and redeploy

3. **Option C: Use older asyncpg version**
   - The requirements.txt now uses `asyncpg==0.28.0` (more compatible)

### **Common Build Errors:**

- **asyncpg compilation error** → Use Python 3.11.9 or fallback requirements
- **Node.js build fails** → Check frontend directory structure
- **Database connection fails** → Verify Supabase connection string

**Your Hotel Procurement E-catalogue System is ready to deploy! 🚀**

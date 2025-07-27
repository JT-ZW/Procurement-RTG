# Hotel Procurement System

A full-stack multi-tenant procurement system for hotel management with Vue.js frontend and FastAPI backend.

## ✅ Current Status: WORKING

- ✅ Backend API running on http://localhost:8001
- ✅ Vue frontend running on http://localhost:5173
- ✅ JWT Authentication working
- ✅ User login/registration working
- ✅ Frontend-backend integration working

## 🚀 Quick Start

### Start Backend (Required)

```bash
cd backend-clean
# Double-click: start_backend.bat
# OR run manually:
python main_clean.py
```

### Start Frontend

```bash
cd frontend/procurement-frontend
# Double-click: start_frontend.bat
# OR run manually:
npm run dev
```

### Start Both (Recommended)

```bash
# Double-click: start_full_system.bat (in root folder)
```

## 🔐 Test Users

| Email             | Password  | Role    |
| ----------------- | --------- | ------- |
| admin@hotel.com   | secret123 | admin   |
| manager@hotel.com | secret123 | manager |

## 📁 Clean File Structure

### Backend (backend-clean/)

```
backend-clean/
├── main_clean.py          # Main FastAPI server
├── auth_simple.py         # JWT authentication logic
├── requirements_clean.txt # Python dependencies
├── start_backend.bat      # Start backend server
└── .env                   # Environment variables
```

### Frontend (frontend/procurement-frontend/)

```
frontend/procurement-frontend/
├── src/
│   ├── services/
│   │   ├── api.js         # Axios API client (updated for localhost:8001)
│   │   └── auth.js        # Authentication API calls (updated)
│   ├── views/             # Vue pages
│   ├── components/        # Vue components
│   └── main.js
├── package.json
└── start_frontend.bat     # Start Vue dev server
```

## 🌐 API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation
- `POST /auth/login/json` - User login
- `POST /auth/register/json` - User registration
- `GET /auth/me` - Get current user info

## 🔄 Next Steps

1. ✅ **Authentication System** - COMPLETE
2. 🔄 **Add Product Management** - Add CRUD for products
3. 🔄 **Add Purchase Requisitions** - Core procurement workflow
4. 🔄 **Add Multi-tenant Logic** - Hotel unit separation
5. 🔄 **Add Dashboard Analytics** - Usage statistics

## 🛠️ Development

- Backend: FastAPI + JWT + Uvicorn
- Frontend: Vue 3 + Vite + Axios + Bootstrap
- Authentication: JWT tokens with Bearer authorization
- CORS: Configured for localhost development

## 📝 Notes

- Backend runs on port **8001** (not 8000)
- Frontend expects backend on **localhost:8001**
- All authentication working with JWT tokens
- Ready for production with proper environment variables

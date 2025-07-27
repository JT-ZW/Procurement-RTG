"""
API v1 router configuration
"""

from fastapi import APIRouter

from app.api.v1 import auth, users, units, products, suppliers, stock, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(units.router, prefix="/units", tags=["units"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(stock.router, prefix="/stock", tags=["stock"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

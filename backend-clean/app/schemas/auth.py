"""
Authentication Schemas - Token and auth-related models
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel
from app.schemas.user import UserResponse


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    units: List[Dict[str, Any]] = []


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[UUID] = None

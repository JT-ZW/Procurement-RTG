"""
Authentication endpoints for Hotel Procurement System
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import jwt
from datetime import datetime, timedelta

router = APIRouter()
security = HTTPBearer()

# Request models
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    unit: str = "main"

# Mock user database (replace with real database later)
# For testing, using simple plaintext passwords temporarily
MOCK_USERS = {
    "admin@hotel.com": {
        "id": "1",
        "email": "admin@hotel.com",
        "name": "Admin User",
        "password": "secret123",  # Using plaintext for testing
        "role": "admin",
        "unit": "main"
    },
    "manager@hotel.com": {
        "id": "2", 
        "email": "manager@hotel.com",
        "name": "Manager User",
        "password": "secret123",  # Using plaintext for testing
        "role": "manager",
        "unit": "restaurant"
    }
}

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password: str, stored_password: str) -> bool:
    """Verify a plain password against stored password (temporarily using plaintext)."""
    return plain_password == stored_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user data."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = MOCK_USERS.get(email)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/login")
async def login(email: str, password: str):
    """Login endpoint that returns JWT token."""
    print(f"Login attempt: {email} / {password}")  # Debug logging
    
    user = MOCK_USERS.get(email)
    if not user:
        print(f"User not found: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not verify_password(password, user["password"]):
        print(f"Password mismatch for {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    print(f"Login successful for {email}")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "unit": user["unit"]
        }
    }

@router.post("/login/json")
async def login_json(request: LoginRequest):
    """JSON-based login for frontend compatibility."""
    return await login(request.email, request.password)

@router.post("/register/json")
async def register_json(request: RegisterRequest):
    """JSON-based registration for frontend compatibility."""
    return await register(request.email, request.password, request.name, request.unit)

@router.get("/me")
async def get_current_user(current_user: dict = Depends(verify_token)):
    """Get current user information."""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user["name"],
        "role": current_user["role"],
        "unit": current_user["unit"]
    }

@router.post("/register")
async def register(email: str, password: str, name: str, unit: str = "main"):
    """Register a new user."""
    if email in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user (using plaintext password for testing)
    new_user = {
        "id": str(len(MOCK_USERS) + 1),
        "email": email,
        "name": name,
        "password": password,  # Using plaintext for testing
        "role": "user",
        "unit": unit
    }
    
    MOCK_USERS[email] = new_user
    
    return {
        "message": "User registered successfully",
        "user": {
            "id": new_user["id"],
            "email": new_user["email"],
            "name": new_user["name"],
            "role": new_user["role"],
            "unit": new_user["unit"]
        }
    }

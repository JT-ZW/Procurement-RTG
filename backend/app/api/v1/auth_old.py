from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.crud import crud_user
from app.models.user import User
from app.schemas.auth import Token, UserLogin, UserCreate, UserResponse, PasswordReset, PasswordResetRequest
from app.schemas.user import UserUpdate
from app.utils.multi_tenant import get_user_units

router = APIRouter()


@router.post("/login", response_model=Token)
def login_for_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = crud_user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not crud_user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "units": get_user_units(db, user_id=user.id)
    }


@router.post("/login/json", response_model=Token)
def login_json(
    user_in: UserLogin,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    JSON login endpoint for frontend applications.
    """
    user = crud_user.authenticate(
        db, email=user_in.email, password=user_in.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    elif not crud_user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "units": get_user_units(db, user_id=user.id)
    }


@router.post("/register", response_model=UserResponse)
def register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Create new user. Open registration for now.
    """
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    
    user = crud_user.create(db, obj_in=user_in)
    return user


@router.post("/admin/register", response_model=UserResponse)
def admin_register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Create new user by admin. Only accessible by superusers.
    """
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    
    user = crud_user.create(db, obj_in=user_in)
    return user


@router.post("/test-token", response_model=UserResponse)
def test_token(current_user: User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token and return current user info.
    """
    return current_user


@router.post("/refresh-token", response_model=Token)
def refresh_token(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Refresh access token.
    """
    if not crud_user.is_active(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=current_user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": current_user,
        "units": get_user_units(db, user_id=current_user.id)
    }


@router.post("/password-reset-request")
def password_reset_request(
    password_reset_request: PasswordResetRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Request password reset. Sends email with reset token.
    """
    user = crud_user.get_by_email(db, email=password_reset_request.email)
    if not user:
        # Don't reveal whether user exists or not for security
        return {"message": "If the email exists, a password reset link has been sent."}
    
    if not crud_user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Generate password reset token
    password_reset_token = security.generate_password_reset_token(email=user.email)
    
    # TODO: Send email with reset token
    # send_reset_password_email(
    #     email_to=user.email,
    #     email=user.email,
    #     token=password_reset_token
    # )
    
    return {"message": "Password reset email sent"}


@router.post("/password-reset")
def password_reset(
    password_reset: PasswordReset,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Reset password using reset token.
    """
    email = security.verify_password_reset_token(password_reset.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
    
    user = crud_user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not crud_user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    hashed_password = security.get_password_hash(password_reset.new_password)
    user_update = UserUpdate(password=hashed_password)
    crud_user.update(db, db_obj=user, obj_in=user_update)
    
    return {"message": "Password updated successfully"}


@router.post("/logout")
def logout(
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Logout endpoint. In a stateless JWT setup, this is mainly for client-side cleanup.
    For enhanced security, you might want to implement token blacklisting.
    """
    # TODO: Implement token blacklisting if needed
    # blacklist_token(token)
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
def read_users_me(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get current user profile with units.
    """
    user_data = current_user.__dict__.copy()
    user_data["units"] = get_user_units(db, user_id=current_user.id)
    return user_data


@router.put("/me", response_model=UserResponse)
def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Update own user profile.
    """
    # Users can only update certain fields about themselves
    update_data = user_in.dict(exclude_unset=True)
    
    # Remove sensitive fields that users shouldn't be able to update themselves
    restricted_fields = ["role", "is_active", "is_superuser"]
    for field in restricted_fields:
        update_data.pop(field, None)
    
    # If updating password, hash it
    if "password" in update_data:
        update_data["password"] = security.get_password_hash(update_data["password"])
    
    user_update = UserUpdate(**update_data)
    user = crud_user.update(db, db_obj=current_user, obj_in=user_update)
    return user


@router.post("/change-password")
def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Change password (requires current password).
    """
    if not security.verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    hashed_password = security.get_password_hash(new_password)
    user_update = UserUpdate(password=hashed_password)
    crud_user.update(db, db_obj=current_user, obj_in=user_update)
    
    return {"message": "Password changed successfully"}
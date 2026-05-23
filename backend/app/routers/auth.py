# backend/app/routers/auth.py

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from app.services.auth_service import register_user, login_user, get_current_user

router = APIRouter()


@router.post("/auth/register", response_model=UserResponse)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account.
    Password is hashed before storing — never saved as plain text.
    """
    user = register_user(db, data)
    return user


@router.post("/auth/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """
    Login and receive a JWT token.
    
    How JWT works:
    1. User sends email + password
    2. Server verifies credentials
    3. Server returns a signed JWT token
    4. Frontend stores token
    5. Frontend sends token with every future request
    6. Server verifies token signature on every request
    """
    result = login_user(db, data)
    return result


@router.get("/auth/me", response_model=UserResponse)
def get_me(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get current logged-in user profile.
    Requires: Authorization: Bearer <token> header
    """
    if not authorization or not authorization.startswith("Bearer "):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    user  = get_current_user(token, db)
    return user


@router.post("/auth/logout")
def logout():
    """
    Logout endpoint.
    
    WHY no server-side logout with JWT:
    JWT tokens are stateless — the server doesn't track them.
    Logout is handled on the FRONTEND by deleting the stored token.
    
    For true server-side logout you need a token blacklist
    (Redis-based) — that's an advanced pattern.
    """
    return {"message": "Logged out successfully. Delete your token on the client."}
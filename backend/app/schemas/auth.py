# backend/app/schemas/auth.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserRegister(BaseModel):
    email:     EmailStr
    username:  str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    password:  str = Field(..., min_length=6)

    class Config:
        json_schema_extra = {
            "example": {
                "email":     "john@example.com",
                "username":  "john_doe",
                "full_name": "John Doe",
                "password":  "securepassword123"
            }
        }

class UserLogin(BaseModel):
    email:    EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email":    "john@example.com",
                "password": "securepassword123"
            }
        }

class UserResponse(BaseModel):
    id:        int
    email:     str
    username:  str
    full_name: Optional[str]
    is_active: bool
    is_admin:  bool

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token:  str
    token_type:    str = "bearer"
    expires_in:    int  # seconds
    user:          UserResponse
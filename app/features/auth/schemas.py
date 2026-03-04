# app/features/auth/schemas.py
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    password: str = Field(min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SetPinRequest(BaseModel):
    pin: str = Field(min_length=6, max_length=6)
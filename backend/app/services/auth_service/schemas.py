from pydantic import BaseModel, EmailStr

from app.services.user_service.schemas import UserOut


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    user: UserOut
    tokens: TokenPair


class RefreshIn(BaseModel):
    refresh_token: str
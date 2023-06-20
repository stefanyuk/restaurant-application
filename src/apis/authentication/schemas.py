from pydantic import BaseModel, EmailStr


class AccessToken(BaseModel):
    access: str


class RefreshToken(BaseModel):
    refresh: str


class TokensData(RefreshToken, AccessToken):
    """Schema representing authorization tokens for the user."""

    refresh: str
    access: str


class UserEmail(BaseModel):
    email: EmailStr

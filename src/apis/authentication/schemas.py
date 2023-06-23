from pydantic import BaseModel
from src.apis.users.schemas import UserBaseSchema


class AccessToken(BaseModel):
    access: str


class RefreshToken(BaseModel):
    refresh: str


class TokensData(RefreshToken, AccessToken):
    """Schema representing authorization tokens for the user."""

    refresh: str
    access: str


class SignUpResponseSchema(BaseModel):
    tokens: TokensData
    user: UserBaseSchema

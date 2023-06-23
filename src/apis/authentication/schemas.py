from pydantic import BaseModel
from src.apis.users.schemas import UserBaseSchema


class AccessToken(BaseModel):
    access_token: str


class RefreshToken(BaseModel):
    refresh_token: str


class TokensData(RefreshToken, AccessToken):
    """Schema representing authorization tokens for the user."""

    token_type: str = "bearer"


class SignUpResponseSchema(BaseModel):
    tokens: TokensData
    user: UserBaseSchema

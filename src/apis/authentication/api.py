from fastapi import APIRouter, status, Depends
from src.apis.token_backend import create_jwt_token_backend, APITokenBackend
from src.apis.common_errors import InvalidToken, build_http_exception_response
from src.apis.services.user_service import UserService, UserDoesNotExist

from src.database.db import get_db_session
from sqlalchemy.orm import Session
from src.settings import settings
from src.apis.authentication.schemas import RefreshToken, TokensData, UserEmail

ROUTER = APIRouter(prefix="/auth", tags=["auth"])


@ROUTER.post("/token", response_model=TokensData)
def get_tokens_for_user(
    user_email_data: UserEmail,
    db_session: Session = Depends(get_db_session),
    token_backend: APITokenBackend = Depends(create_jwt_token_backend),
):
    """Create and return a new access and refresh tokens for the user."""

    service = UserService(db_session)
    user = service.get_by_field_value("email", user_email_data.email)

    if user is None:
        return build_http_exception_response(
            message="User with given email not found",
            code=status.HTTP_404_NOT_FOUND,
        )

    access_token = token_backend.create_api_token_for_user(
        user, settings.access_token_lifetime
    )
    refresh_token = token_backend.create_api_token_for_user(
        user, settings.refresh_token_lifetime
    )

    return {"access": access_token, "refresh": refresh_token}


@ROUTER.post("/refresh")
def refresh_token(
    token: RefreshToken,
    db_session: Session = Depends(get_db_session),
    token_backend: APITokenBackend = Depends(create_jwt_token_backend),
):
    """Create new access token in case if provided refresh token is valid."""
    service = UserService(db_session)

    try:
        payload = token_backend.verify(token.refresh)
    except InvalidToken:
        return build_http_exception_response(
            message="Refresh token is invalid", code=status.HTTP_401_UNAUTHORIZED
        )

    try:
        user = service.get_by_id(payload[settings.user_id_claim_name])
    except UserDoesNotExist as error:
        return build_http_exception_response(
            message=error.message,
            code=status.HTTP_404_NOT_FOUND,
        )

    access_token = token_backend.create_api_token_for_user(
        user, settings.access_token_lifetime
    )

    return {"access": access_token}

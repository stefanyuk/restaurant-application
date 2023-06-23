from typing import Annotated
from fastapi import APIRouter, status, Depends
from src.apis.token_backend import (
    create_jwt_token_backend,
    APITokenBackend,
    InvalidToken,
)
from src.apis.common_errors import build_http_exception_response, ErrorResponse
from src.apis.services.user_service import (
    UserService,
    UserDoesNotExist,
    UserAlreadyExists,
)
from fastapi.security import OAuth2PasswordRequestForm
from src.database.db import get_db_session
from sqlalchemy.orm import Session
from src.settings import settings
from src.apis.authentication.schemas import (
    RefreshToken,
    TokensData,
    AccessToken,
    SignUpResponseSchema,
)
from src.apis.users.schemas import UserCreateSchema

ROUTER = APIRouter(prefix="/auth", tags=["auth"])


@ROUTER.post(
    "/signup",
    response_model=SignUpResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"model": SignUpResponseSchema},
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
    },
)
def create_user_api(
    user_data: UserCreateSchema,
    db_session: Session = Depends(get_db_session),
    token_backend: APITokenBackend = Depends(create_jwt_token_backend),
):
    service = UserService(db_session)

    try:
        user = service.create_user(user_data)
    except UserAlreadyExists as error:
        return build_http_exception_response(
            message=error.message,
            code=status.HTTP_400_BAD_REQUEST,
        )

    access_token = token_backend.create_api_token_for_user(
        user, settings.access_token_lifetime
    )
    refresh_token = token_backend.create_api_token_for_user(
        user, settings.refresh_token_lifetime
    )

    return {
        "user": user,
        "tokens": {"access_token": access_token, "refresh_token": refresh_token},
    }


@ROUTER.post(
    "/login",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": TokensData},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    },
    response_model=TokensData,
)
def get_tokens_for_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db_session: Session = Depends(get_db_session),
    token_backend: APITokenBackend = Depends(create_jwt_token_backend),
):
    """Create and return a new access and refresh tokens after successful login."""
    service = UserService(db_session)
    user = service.get_by_field_value("email", form_data.username)

    if user is None or not user.verify_password(form_data.password, user.password_hash):
        return build_http_exception_response(
            message="Incorrect username or password",
            code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = token_backend.create_api_token_for_user(
        user, settings.access_token_lifetime
    )
    refresh_token = token_backend.create_api_token_for_user(
        user, settings.refresh_token_lifetime
    )

    return {"access_token": access_token, "refresh_token": refresh_token}


@ROUTER.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    response_model=AccessToken,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    },
)
def refresh_token(
    token: RefreshToken,
    db_session: Session = Depends(get_db_session),
    token_backend: APITokenBackend = Depends(create_jwt_token_backend),
):
    """Create new access token in case if provided refresh token is valid."""
    service = UserService(db_session)

    try:
        payload = token_backend.verify(token.refresh_token)
    except InvalidToken:
        return build_http_exception_response(
            message="Refresh token is invalid", code=status.HTTP_401_UNAUTHORIZED
        )

    try:
        user = service.get_by_id(payload[settings.user_id_claim_name])
    except UserDoesNotExist:
        return build_http_exception_response(
            message="Refresh token is invalid", code=status.HTTP_401_UNAUTHORIZED
        )

    access_token = token_backend.create_api_token_for_user(
        user, settings.access_token_lifetime
    )

    return {"access_token": access_token}

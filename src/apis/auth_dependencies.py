from datetime import datetime

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.apis.services.user_service import UserService
from src.apis.token_backend import (
    APITokenBackend,
    InvalidToken,
    create_jwt_token_backend,
)
from src.database.db import get_db_session
from src.database.models import User
from src.apis.common_errors import build_http_exception_response


def authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db_session: Session = Depends(get_db_session),
    token_backend: APITokenBackend = Depends(create_jwt_token_backend),
) -> User:
    """Protect API endpoints with JWT token authentication."""
    service = UserService(db_session)

    if credentials is not None:
        try:
            user = token_backend.get_user_from_token(credentials.credentials, service)
        except InvalidToken:
            return build_http_exception_response(
                message="Token is not valid.", code=status.HTTP_403_FORBIDDEN
            )
    else:
        return build_http_exception_response(
            message="Not authenticated.", code=status.HTTP_403_FORBIDDEN
        )

    service.update_user_last_login_date(user.id, new_last_login_time=datetime.utcnow())

    return user


def authenticated_admin_user(user: User = Depends(authenticated_user)):
    if user.is_admin is False:
        return build_http_exception_response(
            message="Access denied.", code=status.HTTP_403_FORBIDDEN
        )

    return user

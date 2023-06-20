from datetime import datetime

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from sqlalchemy.orm import Session

from src.apis.admin.users.schemas import UserExtendedCreate
from src.apis.services.user_service import UserService
from src.apis.token_backend import APITokenBackend, JWTTokenBackend, InvalidToken
from src.database.db import get_db_session
from src.database.models import User
from src.apis.common_errors import build_http_exception_response


def authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db_session: Session = Depends(get_db_session),
    token_backend: APITokenBackend = Depends(JWTTokenBackend(jwt)),
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


def debug_auth(db_session: Session):
    service = UserService(db_session)
    user = service.get_by_field_value("email", "admin@example.com")
    if user is None:
        user_data = {
            "password": "stringst",
            "first_name": "admin",
            "last_name": "admin",
            "email": "admin@example.com",
            "birth_date": datetime(2023, 6, 8),
            "is_admin": True,
            "is_employee": True,
        }
        return service.create_user(UserExtendedCreate.parse_obj(user_data))

    return user

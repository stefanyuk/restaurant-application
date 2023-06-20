from fastapi import Depends, APIRouter, status

from src.apis.admin.users.schemas import UserExtendedCreate, UserExtendedOut
from fastapi_pagination.limit_offset import LimitOffsetPage
from typing import Optional
from src.apis.common_errors import ErrorResponse, build_http_exception_response
from src.database.db import get_db_session
from sqlalchemy.orm import Session
from src.apis.services.user_service import (
    UserAlreadyExists,
    UserDoesNotExist,
    UserService,
)

ROUTER = APIRouter(prefix="/users")


@ROUTER.post(
    "/",
    responses={
        status.HTTP_200_OK: {"model": UserExtendedOut},
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
    },
)
def create_user_by_admin_api(
    user_data: UserExtendedCreate, db_session: Session = Depends(get_db_session)
) -> UserExtendedOut:
    service = UserService(db_session)

    try:
        user = service.create_user(user_data)
    except UserAlreadyExists as error:
        return build_http_exception_response(
            message=error.message,
            code=status.HTTP_400_BAD_REQUEST,
        )

    return user


@ROUTER.get("/")
def get_users_list_api(
    search: Optional[str] = None,
    sort: Optional[str] = None,
    db_session: Session = Depends(get_db_session),
) -> LimitOffsetPage[UserExtendedOut]:
    """Return list of all existing User entities."""
    service = UserService(db_session)
    return service.read_all(search, sort)


@ROUTER.get(
    "/{user_id}",
    responses={
        status.HTTP_200_OK: {"model": UserExtendedOut},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    },
)
def get_user_api(
    user_id: int, db_session: Session = Depends(get_db_session)
) -> UserExtendedOut:
    """Return information about user with the provided id."""
    service = UserService(db_session)

    try:
        user = service.get_by_id(user_id)
    except UserDoesNotExist as error:
        return build_http_exception_response(
            message=error.message,
            code=status.HTTP_404_NOT_FOUND,
        )

    return user


@ROUTER.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_api(
    user_id: int,
    db_session: Session = Depends(get_db_session),
):
    service = UserService(db_session)
    service.delete(user_id)

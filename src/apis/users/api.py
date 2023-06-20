from fastapi import APIRouter, Body, Depends, status
from pydantic import EmailStr
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from src.apis.auth_dependencies import authenticated_user
from src.apis.common_errors import ErrorResponse, build_http_exception_response
from src.apis.services.order_service import OrderService, ProductDoesNotExist
from src.apis.services.user_service import (
    UserAlreadyExists,
    UserService,
)
from src.apis.services.email_service import (
    send_order_creation_notification_email,
    send_password_reset_email,
)
from src.apis.users.schemas import (
    AddressBase,
    AddressOut,
    OrderCreate,
    OrderOut,
    UpdateUser,
    UserCreate,
    UserOut,
    PasswordReset,
)
from src.database.db import get_db_session
from src.database.models import User
from src.apis.token_backend import (
    create_jwt_token_backend,
    InvalidToken,
    APITokenBackend,
)
from src.apis.services.email_service import fm


USERS_ROUTER = APIRouter(prefix="/users", tags=["users"])
ME_ROUTER = APIRouter(prefix="/me", tags=["me"])


@USERS_ROUTER.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"model": UserOut},
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
    },
)
def create_user_api(
    user_data: UserCreate,
    db_session: Session = Depends(get_db_session),
) -> UserOut:
    service = UserService(db_session)

    try:
        user = service.create_user(user_data)
    except UserAlreadyExists as error:
        return build_http_exception_response(
            message=error.message,
            code=status.HTTP_400_BAD_REQUEST,
        )

    return user


@USERS_ROUTER.post("/password", status_code=status.HTTP_202_ACCEPTED)
async def obtain_reset_password_email(
    background_tasks: BackgroundTasks,
    email: EmailStr = Body(..., embed=True),
    db_session: Session = Depends(get_db_session),
    token_backend: APITokenBackend = Depends(create_jwt_token_backend),
):
    service = UserService(db_session)
    user = service.get_by_field_value("email", email)

    if user is None:
        raise build_http_exception_response(
            f"User with email '{email}' does not exist.",
            code=status.HTTP_400_BAD_REQUEST,
        )

    background_tasks.add_task(send_password_reset_email, user, token_backend, fm)


@USERS_ROUTER.patch(
    "/password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
    },
)
def reset_user_password(
    reset_password_data: PasswordReset,
    db_session: Session = Depends(get_db_session),
    token_backend: APITokenBackend = Depends(create_jwt_token_backend),
):
    service = UserService(db_session)

    try:
        user = token_backend.get_user_from_token(reset_password_data.token, service)
    except InvalidToken:
        raise build_http_exception_response(
            "The provided token is not valid.", status.HTTP_400_BAD_REQUEST
        )

    service.update_user_data(user.id, {"password": reset_password_data.password})


@ME_ROUTER.get(
    "/",
    responses={
        status.HTTP_200_OK: {"model": UserOut},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    },
)
def get_authenticated_user_info(user: User = Depends(authenticated_user)) -> UserOut:
    """Return information about currently authenticated user."""
    return user


@ME_ROUTER.patch(
    "/",
    responses={
        status.HTTP_200_OK: {"model": UserOut},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    },
)
def update_authenticated_user_info(
    update_data: UpdateUser,
    user: User = Depends(authenticated_user),
    db_session: Session = Depends(get_db_session),
) -> UserOut:
    """Update information about currently authenticated user."""
    service = UserService(db_session)

    try:
        user = service.update_user_data(user.id, update_data.dict(exclude_unset=True))
    except UserAlreadyExists as error:
        return build_http_exception_response(
            message=error.message,
            code=status.HTTP_400_BAD_REQUEST,
        )

    return user


@ME_ROUTER.post(
    "/addresses",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"model": AddressOut},
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    },
)
def create_authenticated_user_address_api(
    address_data: AddressBase,
    user: User = Depends(authenticated_user),
    db_session: Session = Depends(get_db_session),
) -> AddressOut:
    service = UserService(db_session)
    address = service.add_address(user, address_data)
    return address


@ME_ROUTER.post(
    "/orders",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"model": OrderOut},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
    },
)
async def create_authenticated_user_order_api(
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(authenticated_user),
    db_session: Session = Depends(get_db_session),
) -> OrderOut:
    order_service = OrderService(db_session)
    user_service = UserService(db_session)
    address = user_service.add_address(user, order_data.delivery_address)

    try:
        order = order_service.create_order(user, order_data, address)
    except ProductDoesNotExist as error:
        return build_http_exception_response(
            message=error.message,
            code=status.HTTP_400_BAD_REQUEST,
        )

    background_tasks.add_task(send_order_creation_notification_email, user, order, fm)

    return order

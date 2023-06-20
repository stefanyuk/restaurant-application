from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from src.apis.auth_dependencies import authenticated_user
from src.apis.common_errors import ErrorResponse, build_http_exception_response
from src.apis.services.order_service import OrderService, ProductDoesNotExist
from src.apis.services.user_service import (
    UserAlreadyExists,
    UserDoesNotExist,
    UserService,
)
from src.apis.services.email_service import send_order_creation_notification_email
from src.apis.users.schemas import (
    AddressBase,
    AddressOut,
    OrderCreate,
    OrderOut,
    UpdateUser,
    UserCreate,
    UserOut,
)
from src.database.db import get_db_session
from src.database.models import User

USERS_ROUTER = APIRouter(prefix="/users", tags=["users"])
ME_ROUTER = APIRouter(prefix="/me", tags=["me"])


@USERS_ROUTER.post(
    "/",
    responses={
        status.HTTP_200_OK: {"model": UserOut},
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
    except UserDoesNotExist as error:
        return build_http_exception_response(
            message=error.message,
            code=status.HTTP_404_NOT_FOUND,
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

    background_tasks.add_task(
        send_order_creation_notification_email, user, order, address
    )

    return order

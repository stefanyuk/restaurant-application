from fastapi import APIRouter, Body, Depends, status
from fastapi_pagination import LimitOffsetPage
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
    AddressSchema,
    AddressBaseSchema,
    OrderCreateSchema,
    UpdateUserSchema,
    UserCreateSchema,
    PasswordResetSchema,
    UserOutSchema,
    OrderOutSchema,
    AddressOutSchema,
    AddressUpdateSchema,
    OrderFilterParamsSchema,
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
    response_model=UserOutSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"model": UserOutSchema},
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
    },
)
def create_user_api(
    user_data: UserCreateSchema,
    db_session: Session = Depends(get_db_session),
):
    service = UserService(db_session)

    try:
        user = service.create_user(user_data)
    except UserAlreadyExists as error:
        return build_http_exception_response(
            message=error.message,
            code=status.HTTP_400_BAD_REQUEST,
        )

    return {"user": user}


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
            code=status.HTTP_404_NOT_FOUND,
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
    reset_password_data: PasswordResetSchema,
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
    response_model=UserOutSchema,
    responses={
        status.HTTP_200_OK: {"model": UserOutSchema},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    },
)
def get_authenticated_user_info(
    user: User = Depends(authenticated_user),
    db_session: Session = Depends(get_db_session),
):
    """Return information about currently authenticated user."""
    service = UserService(db_session)
    user_delivery_address = service.get_user_delivery_address(user)
    return {"user": user, "delivery_address": user_delivery_address}


@ME_ROUTER.patch(
    "/",
    response_model=UserOutSchema,
    responses={
        status.HTTP_200_OK: {"model": UserOutSchema},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    },
)
def update_authenticated_user_info(
    update_data: UpdateUserSchema,
    user: User = Depends(authenticated_user),
    db_session: Session = Depends(get_db_session),
):
    """Update information about currently authenticated user."""
    service = UserService(db_session)

    try:
        user = service.update_user_data(user.id, update_data.dict(exclude_unset=True))
    except UserAlreadyExists as error:
        return build_http_exception_response(
            message=error.message,
            code=status.HTTP_400_BAD_REQUEST,
        )

    return {"user": user}


@ME_ROUTER.post(
    "/addresses",
    status_code=status.HTTP_201_CREATED,
    response_model=AddressOutSchema,
    responses={
        status.HTTP_201_CREATED: {"model": AddressBaseSchema},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    },
)
def create_authenticated_user_address_api(
    address_data: AddressSchema,
    user: User = Depends(authenticated_user),
    db_session: Session = Depends(get_db_session),
):
    """Create an address for an authenticated user.

    Endpoint does not create an address, in case when
    exact same address already exists in user's address list.
    """
    service = UserService(db_session)
    address = service.add_address(user, address_data)
    return {"delivery_address": address}


@ME_ROUTER.post(
    "/orders",
    response_model=OrderOutSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"model": OrderOutSchema},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
    },
)
async def create_authenticated_user_order_api(
    order: OrderCreateSchema,
    delivery_address: AddressSchema,
    background_tasks: BackgroundTasks,
    user: User = Depends(authenticated_user),
    db_session: Session = Depends(get_db_session),
):
    """Create order for an authenticated user."""
    order_service = OrderService(db_session)
    user_service = UserService(db_session)
    address = user_service.add_address(user, delivery_address)

    try:
        new_order = order_service.create_order(user, order, address)
    except ProductDoesNotExist as error:
        return build_http_exception_response(
            message=error.message,
            code=status.HTTP_400_BAD_REQUEST,
        )

    background_tasks.add_task(
        send_order_creation_notification_email, user, new_order, fm
    )

    return {"order": new_order, "delivery_address": address}


@ME_ROUTER.patch(
    "/addresses/{address_id}",
    status_code=status.HTTP_200_OK,
    response_model=AddressOutSchema,
    responses={
        status.HTTP_201_CREATED: {"model": AddressBaseSchema},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
    },
)
def update_auth_user_address(
    address_id: int,
    address_data: AddressUpdateSchema,
    db_session: Session = Depends(get_db_session),
    user: User = Depends(authenticated_user),
):
    """Update Address entity with the given ID if exists."""

    service = UserService(db_session)
    user_address = service.get_user_delivery_address(user, address_id)

    if user_address is None:
        return build_http_exception_response(
            f"Address with id '{address_id}' does not exist.",
            code=status.HTTP_400_BAD_REQUEST,
        )

    updated_address = service.update_user_address_data(
        user_address, address_data.dict(exclude_unset=True)
    )

    return {"delivery_address": updated_address}


@ME_ROUTER.get(
    "/orders",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
    },
)
def get_auth_user_orders(
    filters: OrderFilterParamsSchema = Depends(OrderFilterParamsSchema),
    db_session: Session = Depends(get_db_session),
    user: User = Depends(authenticated_user),
) -> LimitOffsetPage[OrderOutSchema]:
    service = OrderService(db_session)
    order_filters = {**filters.dict(exclude={"sort"}), "user_id": user.id}
    return service.read_all(filters.sort, filters=order_filters)

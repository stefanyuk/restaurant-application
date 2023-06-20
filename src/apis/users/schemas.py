from datetime import date, datetime
from typing import Optional
import phonenumbers
from phonenumbers import NumberParseException
from pydantic import BaseModel, EmailStr, Field, validator

from src.database.models.constants import MAX_FIRST_NAME_LENGTH, MAX_LAST_NAME_LENGTH
from src.database.models.order import OrderStatus

MIN_PASSWORD_LENGTH = 8


class AddressId(BaseModel):
    id: int


class AddressBase(BaseModel):
    city: str
    street: str
    street_number: int = Field(..., gt=0)
    postal_code: str

    class Config:
        orm_mode = True


class AddressOut(AddressBase, AddressId):
    class Config:
        orm_mode = True


def check_phone_number(phone_number: str | None) -> str | None:
    """Validate whether provided phone number is correct.

    Args:
        phone_number (str | None): provided phone number value or None

    Raises:
        ValueError: in case when provided phone number is incorrect

    Returns:
        str: phone number
    """
    if phone_number is None:
        return phone_number

    is_valid = None

    try:
        number = phonenumbers.parse(phone_number)
        if not phonenumbers.is_valid_number(number):
            is_valid = False
    except NumberParseException:
        is_valid = False

    if is_valid is False:
        raise ValueError("Provided phone number is incorrect.")

    return phone_number


class UserId(BaseModel):
    id: int


class UserPassword(BaseModel):
    password: str


class UserBase(BaseModel):
    first_name: str = Field(..., max_length=MAX_FIRST_NAME_LENGTH)
    last_name: str = Field(..., max_length=MAX_LAST_NAME_LENGTH)
    email: EmailStr
    phone_number: Optional[str] = None
    birth_date: Optional[date] = None

    class Config:
        orm_mode = True


class UserExtended(UserBase):
    is_admin: bool
    is_employee: bool


class UserCreate(UserPassword, UserBase):
    _validate_phone_number = validator("phone_number", allow_reuse=True)(
        check_phone_number
    )


class UserExtendedCreate(UserCreate):
    is_admin: bool
    is_employee: bool


class UserExtendedOut(UserExtended, UserId):
    pass


class UserOut(UserBase, UserId):
    class Config:
        orm_mode = True


class UpdateUser(BaseModel):
    first_name: str = Field(None, max_length=MAX_FIRST_NAME_LENGTH)
    last_name: str = Field(None, max_length=MAX_LAST_NAME_LENGTH)
    email: EmailStr = Field(None)
    phone_number: str = Field(None)
    birth_date: date = Field(None)

    _validate_phone_number = validator("phone_number", allow_reuse=True)(
        check_phone_number
    )


class OrderItemData(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)

    class Config:
        orm_mode = True


class OrderId(BaseModel):
    id: int


class OrderBase(BaseModel):
    comments: Optional[str] = None
    order_items: list[OrderItemData]

    class Config:
        orm_mode = True

    @validator("order_items")
    def validate_if_product_ids_are_unique(cls, order_items_data):
        received_ids = [item.product_id for item in order_items_data]
        unique_ids = set(received_ids)

        if len(unique_ids) != len(received_ids):
            raise ValueError("Order items must be unique.")

        return order_items_data


class OrderCreate(OrderBase):
    delivery_address: AddressBase


class OrderOut(OrderBase, OrderId):
    user_id: int
    status: OrderStatus
    ordered_at: datetime
    delivery_address: AddressBase

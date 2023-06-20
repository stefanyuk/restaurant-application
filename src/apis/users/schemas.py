from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator

from src.database.models.constants import MAX_FIRST_NAME_LENGTH, MAX_LAST_NAME_LENGTH
from src.database.models.order import OrderStatus
from src.apis.utils import check_phone_number


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


class UserId(BaseModel):
    id: int


class UserPassword(BaseModel):
    password: str = Field(..., min_length=MIN_PASSWORD_LENGTH)


class UserBase(BaseModel):
    first_name: str = Field(..., max_length=MAX_FIRST_NAME_LENGTH)
    last_name: str = Field(..., max_length=MAX_LAST_NAME_LENGTH)
    email: EmailStr
    phone_number: Optional[str] = None
    birth_date: Optional[date] = None

    class Config:
        orm_mode = True


class UserCreate(UserPassword, UserBase):
    _validate_phone_number = validator("phone_number", allow_reuse=True)(
        check_phone_number
    )


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

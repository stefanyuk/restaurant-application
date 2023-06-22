from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator

from src.database.models.constants import MAX_FIRST_NAME_LENGTH, MAX_LAST_NAME_LENGTH
from src.database.models.order import OrderStatus
from src.apis.utils import check_phone_number, check_if_value_is_not_empty


MIN_PASSWORD_LENGTH = 8


class AddressId(BaseModel):
    id: int


class AddressBase(BaseModel):
    city: str = Field(..., min_length=1)
    street: str = Field(..., min_length=1)
    street_number: int = Field(..., gt=0)
    postal_code: str = Field(..., min_length=1)

    class Config:
        orm_mode = True


class AddressOut(AddressBase, AddressId):
    class Config:
        orm_mode = True


class UserId(BaseModel):
    id: int


class UserPassword(BaseModel):
    password: str = Field(..., min_length=MIN_PASSWORD_LENGTH)


class UserSchema(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=MAX_FIRST_NAME_LENGTH)
    last_name: str = Field(..., min_length=1, max_length=MAX_LAST_NAME_LENGTH)
    email: EmailStr
    phone_number: Optional[str] = None
    birth_date: Optional[date] = None

    class Config:
        orm_mode = True

    _validate_first_name = validator("first_name", allow_reuse=True)(
        check_if_value_is_not_empty
    )
    _validate_last_name = validator("last_name", allow_reuse=True)(
        check_if_value_is_not_empty
    )


class UserCreate(UserPassword, UserSchema):
    _validate_phone_number = validator("phone_number", allow_reuse=True)(
        check_phone_number
    )


class UserBaseSchema(UserSchema, UserId):
    class Config:
        orm_mode = True


class UserOutSchema(BaseModel):
    user: UserBaseSchema


class UpdateUserSchema(BaseModel):
    first_name: str = Field(None, max_length=MAX_FIRST_NAME_LENGTH)
    last_name: str = Field(None, max_length=MAX_LAST_NAME_LENGTH)
    email: EmailStr = Field(None)
    phone_number: str = Field(None)
    birth_date: date = Field(None)

    _validate_phone_number = validator("phone_number", allow_reuse=True)(
        check_phone_number
    )


class OrderItemSchema(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)

    class Config:
        orm_mode = True


class OrderId(BaseModel):
    id: int


class OrderSchema(BaseModel):
    comments: Optional[str] = None
    order_items: list[OrderItemSchema]

    class Config:
        orm_mode = True

    @validator("order_items")
    def validate_if_product_ids_are_unique(cls, order_items_data):
        received_ids = [item.product_id for item in order_items_data]
        unique_ids = set(received_ids)

        if len(unique_ids) != len(received_ids):
            raise ValueError("Order items must be unique.")

        return order_items_data


class OrderCreateSchema(OrderSchema):
    pass


class OrderBaseSchema(OrderSchema, OrderId):
    user_id: int
    status: OrderStatus
    ordered_at: datetime
    delivery_address: AddressBase


class OrderOutSchema(BaseModel):
    order: OrderBaseSchema


class PasswordReset(UserPassword):
    token: str

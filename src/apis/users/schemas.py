from datetime import date, datetime
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, Field, validator
from src.apis.schemas import BaseFilterParams
from pydantic.utils import GetterDict
from src.database.models.constants import MAX_FIRST_NAME_LENGTH, MAX_LAST_NAME_LENGTH
from src.database.models.order import Order, OrderStatus
from src.apis.utils import (
    check_phone_number,
    check_if_value_is_not_empty,
    check_provided_sort_field,
)


MIN_PASSWORD_LENGTH = 8


class OrderOuterGetter(GetterDict):
    """Class to provide a dictionary-like interface to outer order response.

    This object is created to properly embed return data.
    """

    def get(self, key: str, default: Any) -> Any:
        if key == "order":
            return self._obj
        elif key == "delivery_address":
            return self._obj.Order.delivery_address


class OrderBaseGetter(GetterDict):
    """Class to provide a dictionary-like interface to outer order base response.

    Since paginator returns 'Raw' object instead of 'Order' object, this
    should be properly handled when getting data for encoding.
    """

    def get(self, key: str, default: Any) -> Any:
        if isinstance(self._obj, Order):
            return getattr(self._obj, key, default)
        else:
            if key != "total_price":
                return getattr(self._obj.Order, key, default)
            return getattr(self._obj, key, default)


class AddressId(BaseModel):
    id: int


class AddressSchema(BaseModel):
    city: str = Field(..., min_length=1)
    street: str = Field(..., min_length=1)
    street_number: int = Field(..., gt=0)
    postal_code: str = Field(..., min_length=1)

    class Config:
        orm_mode = True


class AddressBaseSchema(AddressSchema, AddressId):
    class Config:
        orm_mode = True


class AddressUpdateSchema(BaseModel):
    city: Optional[str] = Field(None, min_length=1)
    street: Optional[str] = Field(None, min_length=1)
    street_number: Optional[int] = Field(None, gt=0)
    postal_code: Optional[str] = Field(None, min_length=1)


class AddressOutSchema(BaseModel):
    delivery_address: AddressBaseSchema


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


class UserCreateSchema(UserPassword, UserSchema):
    _validate_phone_number = validator("phone_number", allow_reuse=True)(
        check_phone_number
    )


class UserBaseSchema(UserSchema, UserId):
    class Config:
        orm_mode = True


class UserOutSchema(BaseModel):
    user: UserBaseSchema
    delivery_address: Optional[AddressBaseSchema]


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
    total_price: int

    class Config:
        getter_dict = OrderBaseGetter
        json_encoders = {OrderStatus: lambda status: status.name}


class OrderOutSchema(BaseModel):
    order: OrderBaseSchema
    delivery_address: AddressBaseSchema

    class Config:
        orm_mode = True
        getter_dict = OrderOuterGetter


class PasswordResetSchema(UserPassword):
    token: str


class OrderFilterParamsSchema(BaseFilterParams):
    @validator("sort")
    def validate_sort(cls, value):
        return check_provided_sort_field(Order.SORTABLE_FIELDS, value)

from typing import Optional
from pydantic import BaseModel, validator
from src.apis.utils import check_phone_number
from src.apis.users.schemas import UserSchema, UserId, UserPassword


class UserExtendedBaseSchema(UserSchema):
    is_admin: Optional[bool] = None
    is_employee: Optional[bool] = None


class UserExtendedCreateSchema(UserPassword, UserExtendedBaseSchema):
    _validate_phone_number = validator("phone_number", allow_reuse=True)(
        check_phone_number
    )


class UserExtendedSchema(UserExtendedBaseSchema, UserId):
    pass


class UserExtendedOutSchema(BaseModel):
    user: UserExtendedSchema

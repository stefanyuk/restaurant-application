from typing import Optional
from pydantic import validator
from src.apis.utils import check_phone_number
from src.apis.users.schemas import UserSchema, UserId, UserPassword


class UserExtended(UserSchema):
    is_admin: Optional[bool] = None
    is_employee: Optional[bool] = None


class UserExtendedCreate(UserPassword, UserExtended):
    _validate_phone_number = validator("phone_number", allow_reuse=True)(
        check_phone_number
    )


class UserExtendedOut(UserExtended, UserId):
    pass

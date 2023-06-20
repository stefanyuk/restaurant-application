from pydantic import validator
from src.apis.utils import check_phone_number
from src.apis.users.schemas import UserBase, UserId, UserPassword


class UserExtended(UserBase):
    is_admin: bool
    is_employee: bool


class UserExtendedCreate(UserPassword, UserExtended):
    _validate_phone_number = validator("phone_number", allow_reuse=True)(
        check_phone_number
    )


class UserExtendedOut(UserExtended, UserId):
    pass
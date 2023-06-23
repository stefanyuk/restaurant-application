from typing import Any, Optional
from pydantic import BaseModel, validator
from pydantic.utils import GetterDict
from src.apis.schemas import BaseFilterParams
from src.database.models import User
from src.apis.utils import check_phone_number, check_provided_sort_field
from src.apis.users.schemas import UserSchema, UserId, UserPassword


class UserExtendedOuterGetter(GetterDict):
    """Class to provide a dictionary-like interface to outer user response.

    This object is created to properly embed return data.
    """

    def get(self, key: str, default: Any) -> Any:
        return self._obj


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

    class Config:
        orm_mode = True
        getter_dict = UserExtendedOuterGetter


class UserExtendedFilterParams(BaseFilterParams):
    @validator("sort")
    def validate_sort(cls, value):
        return check_provided_sort_field(User.SORTABLE_FIELDS, value)

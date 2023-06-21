from pydantic import BaseModel, Field, validator

from src.database.models.constants import MAX_CATEGORY_NAME_LENGTH
from src.apis.utils import check_if_value_is_not_empty


class CategoryId(BaseModel):
    id: int


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=MAX_CATEGORY_NAME_LENGTH)

    class Config:
        orm_mode = True

    _validate_name = validator("name", allow_reuse=True)(check_if_value_is_not_empty)


class CategoryCreate(CategoryBase):
    pass


class CategoryOut(CategoryBase, CategoryId):
    pass

from typing import Any
from pydantic import BaseModel, Field, validator
from src.apis.schemas import BaseFilterParams
from pydantic.utils import GetterDict
from src.database.models import Category
from src.database.models.constants import MAX_CATEGORY_NAME_LENGTH
from src.apis.utils import check_if_value_is_not_empty, check_provided_sort_field


class CategoryOuterGetter(GetterDict):
    """Class to provide a dictionary-like interface to outer category response.

    This object is created to properly embed return data.
    """

    def get(self, key: str, default: Any) -> Any:
        return self._obj


class CategoryId(BaseModel):
    id: int


class CategorySchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=MAX_CATEGORY_NAME_LENGTH)

    class Config:
        orm_mode = True

    _validate_name = validator("name", allow_reuse=True)(check_if_value_is_not_empty)


class CategoryCreate(CategorySchema):
    pass


class CategoryBaseSchema(CategorySchema, CategoryId):
    class Config:
        orm_mode = True


class CategoryOutSchema(BaseModel):
    category: CategoryBaseSchema

    class Config:
        getter_dict = CategoryOuterGetter
        orm_mode = True


class CategoryFilterParams(BaseFilterParams):
    @validator("sort")
    def validate_sort(cls, value):
        return check_provided_sort_field(Category.SORTABLE_FIELDS, value)

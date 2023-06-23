from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field, validator
from pydantic.utils import GetterDict
from src.apis.services.picture_saver import PictureFormat
from src.database.models.constants import MAX_PRODUCT_NAME_LENGTH
from src.apis.schemas import BaseFilterParams
from src.database.models import Product
from src.apis.utils import check_provided_sort_field, check_if_value_is_not_empty


class ProductOuterGetter(GetterDict):
    """Class to provide a dictionary-like interface to outer product response.

    This object is created to properly embed return data.
    """

    def get(self, key: str, default: Any) -> Any:
        return self._obj


class PictureData(BaseModel):
    base64_encoded_image: str
    picture_format: PictureFormat


class ProductId(BaseModel):
    id: int


class ProductSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=MAX_PRODUCT_NAME_LENGTH)
    summary: str
    price: Decimal = Field(ge=0.01, decimal_places=2)
    category_id: int = Field(..., ge=1)

    class Config:
        orm_mode = True

    _validate_name = validator("name", allow_reuse=True)(check_if_value_is_not_empty)


class ProductCreate(ProductSchema):
    picture_data: Optional[PictureData] = None


class ProductBaseSchema(ProductSchema, ProductId):
    class Config:
        orm_mode = True


class ProductOutSchema(BaseModel):
    product: ProductBaseSchema

    class Config:
        getter_dict = ProductOuterGetter
        orm_mode = True


class ProductFilterParams(BaseFilterParams):
    @validator("sort")
    def validate_sort(cls, value):
        return check_provided_sort_field(Product.SORTABLE_FIELDS, value)

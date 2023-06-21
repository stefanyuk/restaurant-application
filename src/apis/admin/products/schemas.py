from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, validator

from src.apis.services.picture_saver import PictureFormat
from src.database.models.constants import MAX_PRODUCT_NAME_LENGTH
from src.apis.schemas import BaseFilterParams
from src.database.models import Product
from src.apis.utils import check_provided_sort_field, check_if_value_is_not_empty


class PictureData(BaseModel):
    base64_encoded_image: str
    picture_format: PictureFormat


class ProductId(BaseModel):
    id: int


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=MAX_PRODUCT_NAME_LENGTH)
    summary: str
    price: Decimal = Field(ge=0.01, decimal_places=2)
    category_id: int = Field(..., ge=1)

    class Config:
        orm_mode = True

    _validate_name = validator("name", allow_reuse=True)(check_if_value_is_not_empty)


class ProductCreate(ProductBase):
    picture_data: Optional[PictureData] = None


class ProductOut(ProductBase, ProductId):
    pass


class ProductFilterParams(BaseFilterParams):
    @validator("sort")
    def validate_sort(cls, value):
        return check_provided_sort_field(Product.SORTABLE_FIELDS, value)

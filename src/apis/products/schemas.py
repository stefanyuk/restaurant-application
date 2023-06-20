from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.apis.services.picture_saver import PictureFormat
from src.database.models.constants import MAX_PRODUCT_NAME_LENGTH


class PictureData(BaseModel):
    base64_encoded_image: str
    picture_format: PictureFormat


class ProductId(BaseModel):
    id: int


class ProductBase(BaseModel):
    name: str = Field(..., max_length=MAX_PRODUCT_NAME_LENGTH)
    summary: str
    price: Decimal = Field(ge=0.01, decimal_places=2)
    category_id: int = Field(..., ge=1)

    class Config:
        orm_mode = True


class ProductCreate(ProductBase):
    picture_data: Optional[PictureData] = None


class ProductOut(ProductBase, ProductId):
    pass

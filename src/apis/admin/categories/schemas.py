from pydantic import BaseModel, Field

from src.database.models.constants import MAX_CATEGORY_NAME_LENGTH


class CategoryId(BaseModel):
    id: int


class CategoryBase(BaseModel):
    name: str = Field(..., max_length=MAX_CATEGORY_NAME_LENGTH)

    class Config:
        orm_mode = True


class CategoryCreate(CategoryBase):
    pass


class CategoryOut(CategoryBase, CategoryId):
    pass

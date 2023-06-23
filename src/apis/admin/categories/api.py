from typing import Annotated
from fastapi import APIRouter, Depends, Path, status
from fastapi_pagination.limit_offset import LimitOffsetPage
from sqlalchemy.orm import Session

from src.apis.admin.categories.schemas import (
    CategoryCreate,
    CategoryOutSchema,
    CategoryFilterParams,
)
from src.apis.common_errors import ErrorResponse, build_http_exception_response
from src.apis.services.category_service import CategoryAlreadyExists, CategoryService
from src.database.db import get_db_session


ROUTER = APIRouter(prefix="/categories")


@ROUTER.post(
    "/",
    response_model=CategoryOutSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"model": CategoryOutSchema},
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
    },
)
def create_category_api(
    category_data: CategoryCreate,
    db_session: Session = Depends(get_db_session),
):
    """Create new Category entity."""
    service = CategoryService(db_session)

    try:
        category = service.create_category(category_data)
    except CategoryAlreadyExists as error:
        return build_http_exception_response(
            message=error.message,
            code=status.HTTP_400_BAD_REQUEST,
        )

    return category


@ROUTER.get("/")
def get_categories_list_api(
    filters: Annotated[CategoryFilterParams, Depends()],
    db_session: Session = Depends(get_db_session),
) -> LimitOffsetPage[CategoryOutSchema]:
    """Return list of all existing Category entities."""
    service = CategoryService(db_session)
    return service.read_all(filters.sort, filters.dict(exclude={"sort"}))


@ROUTER.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category_api(
    category_id: int = Path(..., gt=0),
    db_session: Session = Depends(get_db_session),
) -> None:
    """Delete Category entity with the given ID."""
    service = CategoryService(db_session)
    service.delete(category_id)

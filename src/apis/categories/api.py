from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi_pagination.limit_offset import LimitOffsetPage
from sqlalchemy.orm import Session

from src.apis.auth_dependencies import authenticated_user
from src.apis.categories.schemas import CategoryCreate, CategoryOut
from src.apis.common_errors import ErrorResponse, build_http_exception_response
from src.apis.services.category_service import CategoryAlreadyExists, CategoryService
from src.database.db import get_db_session


ROUTER = APIRouter(
    prefix="/categories",
    tags=["categories"],
    dependencies=[Depends(authenticated_user)],
)


@ROUTER.post(
    "/",
    responses={
        status.HTTP_200_OK: {"model": CategoryOut},
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
    },
)
def create_category_api(
    category_data: CategoryCreate,
    db_session: Session = Depends(get_db_session),
) -> CategoryOut:
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
    search: Optional[str] = None,
    sort: Optional[str] = None,
    db_session: Session = Depends(get_db_session),
) -> LimitOffsetPage[CategoryOut]:
    """Return list of all existing Category entities."""
    service = CategoryService(db_session)
    return service.read_all(search, sort)


@ROUTER.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category_api(
    category_id: int,
    db_session: Session = Depends(get_db_session),
) -> None:
    """Delete Category entity with the given ID."""
    service = CategoryService(db_session)
    service.delete(category_id)

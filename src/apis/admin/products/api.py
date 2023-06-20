from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi_pagination.limit_offset import LimitOffsetPage
from sqlalchemy.orm import Session

from src.apis.common_errors import ErrorResponse, build_http_exception_response
from src.apis.admin.products.schemas import ProductCreate, ProductOut
from src.apis.services.category_service import CategoryDoesNotExist, CategoryService
from src.apis.services.picture_saver import ServerPictureSaver
from src.apis.services.product_service import ProductAlreadyExists, ProductService
from src.database.db import get_db_session
from src.settings import settings


ROUTER = APIRouter(prefix="/products")


@ROUTER.post(
    "/",
    responses={
        status.HTTP_200_OK: {"model": ProductOut},
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
    },
)
def create_product_api(
    product_data: ProductCreate,
    db_session: Session = Depends(get_db_session),
) -> ProductOut:
    """Create new Product entity."""
    picture_saver = ServerPictureSaver(settings)
    product_service = ProductService(picture_saver=picture_saver, db_session=db_session)
    category_service = CategoryService(db_session)

    try:
        category_service.get_by_id(product_data.category_id)
    except CategoryDoesNotExist as error:
        return build_http_exception_response(
            message=error.message,
            code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        product = product_service.create_product(product_data)
    except ProductAlreadyExists as error:
        return build_http_exception_response(
            message=error.message,
            code=status.HTTP_400_BAD_REQUEST,
        )

    return product


@ROUTER.get("/")
def get_products_list_api(
    search: Optional[str] = None,
    sort: Optional[str] = None,
    db_session: Session = Depends(get_db_session),
) -> LimitOffsetPage[ProductOut]:
    """Return list of all existing Product entities."""
    service = ProductService(db_session)
    return service.read_all(search, sort)


@ROUTER.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_api(
    product_id: int,
    db_session: Session = Depends(get_db_session),
) -> None:
    """Delete Product entity with the given ID."""
    service = ProductService(db_session)
    service.delete(product_id)

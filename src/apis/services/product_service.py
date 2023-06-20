from sqlalchemy.orm import Session

from src.apis.common_errors import ServiceBaseError
from src.apis.admin.products.schemas import ProductCreate
from src.apis.services.base import BaseService
from src.apis.services.picture_saver import PictureSaver
from src.database.models import Product


class ProductDoesNotExist(ServiceBaseError):
    """Raised in case when product with received id does not exist."""


class ProductAlreadyExists(ServiceBaseError):
    """Raised when product already exists."""


class ProductService(BaseService):
    """Service is responsible for working with the Product entity."""

    model = Product
    db_session: Session
    _entity_not_found_error = ProductDoesNotExist(
        message="Product with the provided id was not found."
    )

    def __init__(self, db_session: Session, picture_saver: PictureSaver | None = None):
        super().__init__(db_session)
        self.picture_saver = picture_saver

    def _check_if_product_exists(self, name: str) -> None:
        product = self.get_by_field_value("name", name)

        if product is not None:
            raise ProductAlreadyExists(
                message=f"Product with name '{name}' already exists."
            )

    def create_product(self, product_data: ProductCreate) -> Product:
        """Create and persist new product.

        Args:
            product_data (ProductCreate): new product data

        Returns:
            Product: new category instance

        Raises:
            ProductAlreadyExists: in case when product with provided name already exists
        """
        self._check_if_product_exists(product_data.name)
        return super()._create(
            name=product_data.name,
            summary=product_data.summary,
            price=product_data.price,
            category_id=product_data.category_id,
        )

    def _save_product_picture(self):
        pass

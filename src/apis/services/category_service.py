from sqlalchemy.orm import Session

from src.apis.admin.categories.schemas import CategoryCreate
from src.apis.common_errors import ServiceBaseError
from src.apis.services.base import BaseService
from src.database.models import Category


class CategoryDoesNotExist(ServiceBaseError):
    """Raised in case when category with received id does not exist."""


class CategoryAlreadyExists(ServiceBaseError):
    """Raised when category already exists."""


class CategoryService(BaseService):
    """Service is responsible for working with the Category entity."""

    model = Category
    db_session: Session
    _entity_not_found_error = CategoryDoesNotExist(
        message="Category with the provided id was not found."
    )

    def _check_if_category_exists(self, name: str) -> None:
        category = self.get_by_field_value("name", name)

        if category is not None:
            raise CategoryAlreadyExists(
                message=f"Category with name '{name}' already exists."
            )

    def create_category(self, category_data: CategoryCreate) -> Category:
        """Create and persist new category.

        Args:
            category_data (CategoryCreate): new category data

        Returns:
            Category: new category instance

        Raises:
            CategoryAlreadyExists: in case when category with provided name
            already exists
        """
        self._check_if_category_exists(category_data.name)
        return super()._create(name=category_data.name)

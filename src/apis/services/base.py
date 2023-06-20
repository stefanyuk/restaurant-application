from typing import Any, Generic, Type, TypeVar

from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import Select
from sqlalchemy import desc
from src.apis.common_errors import ServiceBaseError
from src.database.models import Base

BaseModel = TypeVar("BaseModel", bound=Base)
DataObject = dict[str, Any]


class BaseService(Generic[BaseModel]):
    """Base service class for all services in the system."""

    model: Type[BaseModel]
    _entity_not_found_error: ServiceBaseError

    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def _create(self, **kwargs) -> BaseModel:
        entity = self.model(**kwargs)
        self.db_session.add(entity)
        self.db_session.flush()
        return entity

    def get_by_field_value(self, field_name: str, value: str) -> BaseModel | None:
        query = self._get_list_query()
        query = query.where(getattr(self.model, field_name) == value)
        return self.db_session.scalars(query).first()

    def get_by_id(self, entity_id: int) -> BaseModel:
        entity = self.db_session.get(self.model, entity_id)

        if entity is None:
            raise self._entity_not_found_error

        return entity

    def read_all(
        self, searched_pattern: str | None, sort: str | None
    ) -> list[BaseModel]:
        """
        Retrieve a list of records from the database.

        Records will be optionally filtered by a search pattern and sorted.

        Args:
            searched_pattern (str | None): A string pattern to filter the records.
                If provided, only records containing the pattern in any of the
                searchable fields will be returned. If None, no filtering will be
                applied.
            sort (str | None): A string indicating the sorting order. If the string
                starts with a hyphen ("-"), the sorting will be in descending order
                based on the specified field. If it does not start with a hyphen,
                the sorting will be in ascending order. If None, no sorting will be
                applied.

        Returns:
            list[BaseModel]: A list of BaseModel objects representing the retrieved
            records.
        """
        query = self._get_list_query()

        if searched_pattern is not None:
            query = self._apply_search_filter(query, searched_pattern)

        if sort is not None:
            query = self._apply_sorting(query, sort)

        return paginate(conn=self.db_session, query=query)

    def update(self, entity: Base, new_data: DataObject) -> BaseModel:
        """Update record in a table."""
        for field_name, value in new_data.items():
            setattr(entity, field_name, value)

        self.db_session.add(entity)
        self.db_session.flush()
        return entity

    def delete(self, entity_id: int) -> None:
        query = self._get_list_query().where(self.model.id == entity_id)
        entity = self.db_session.scalars(query).first()

        if entity is None:
            return

        self.db_session.delete(entity)

    def _apply_search_filter(self, query: Select, searched_pattern: str) -> Select:
        """
        Apply a search filter to the given query based on the provided pattern.

        Args:
            query (Select): The SQLAlchemy Select object representing the query to
                be filtered.
            searched_pattern (str): The pattern to search for in the searchable
                fields.

        Returns:
            Select: The updated SQLAlchemy Select object with the search filter
            applied.
        """
        return query.where(
            or_(
                getattr(self.model, field).ilike(f"%{searched_pattern}%")
                for field in self.model.SEARCHABLE_FIELDS
            )
        )

    def _apply_sorting(self, query: Select, sort: str) -> Select:
        """
        Apply sorting to the given query based on the provided sort parameter.

        Args:
            query (Select): The SQLAlchemy Select object representing the query to
                be sorted.
            sort (str): The sort parameter indicating the sorting order. If the
                string starts with a hyphen ("-"), the sorting will be in
                descending order based on the specified field. If it does not start
                with a hyphen, the sorting will be in ascending order.

        Returns:
            Select: The updated SQLAlchemy Select object with the sorting applied.
        """
        sort_field = sort.lstrip("-")

        if sort.startswith("-"):
            return query.order_by(desc(getattr(self.model, sort_field)))
        else:
            return query.order_by(getattr(self.model, sort_field))

    def _get_list_query(self) -> Select:
        return select(self.model)

from typing import Any, Generic, Type, TypeVar, Mapping

from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import Select
from sqlalchemy import desc
from src.apis.common_errors import ServiceBaseError
from src.database.models import Base

BaseModel = TypeVar("BaseModel", bound=Base)
DataObject = Mapping[str, Any]
FilterData = Mapping[str, Any]


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
        self,
        sort: str | None,
        filters: FilterData,
    ) -> list[BaseModel]:
        """Retrieve a list of records from the database.

        Records will be optionally filtered by a search pattern and sorted.

        Args:
            sort (str | None): A string indicating the sorting order. If the string
                starts with a hyphen ("-"), the sorting will be in descending order
                based on the specified field. If it does not start with a hyphen,
                the sorting will be in ascending order. If None, no sorting will be
                applied.
            filters (FilterData | None, optional): filters to apply to result list

        Returns:
            list[BaseModel]: A list of BaseModel objects representing the retrieved
            records.
        """
        query = self._get_list_query()
        query = self._prepare_read_all_query(query, sort, filters)
        return paginate(conn=self.db_session, query=query)

    def _prepare_read_all_query(
        self,
        query: Select,
        sort: str | None,
        filters: FilterData,
    ) -> Select:
        if any(filters.values()):
            query = self._get_filtered_query(query, filters)

        if sort is not None:
            query = self._apply_sorting(query, sort)

        return query

    def update(self, entity: BaseModel, new_data: DataObject) -> BaseModel:
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

    def _get_filtered_query(self, query: Select, filters: FilterData) -> Select:
        filter_expressions = []

        if searched_pattern := filters.get("search", None):
            filter_expressions.append(
                or_(
                    getattr(self.model, field).ilike(f"%{searched_pattern}%")
                    for field in self.model.SEARCHABLE_FIELDS
                )
            )

        return query.where(*filter_expressions)

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

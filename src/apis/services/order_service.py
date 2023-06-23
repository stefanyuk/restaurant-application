from sqlalchemy import Select, select, text
from sqlalchemy.orm import Session

from src.apis.common_errors import ServiceBaseError
from src.apis.services.base import BaseService, FilterData
from src.database.models import Order, OrderItem, Product, User, Address
from src.apis.users.schemas import OrderCreateSchema, OrderItemSchema
from sqlalchemy.sql import func
from sqlalchemy.sql.selectable import Subquery

TOTAL_PRICE_FIELD = "total_price"


class ProductDoesNotExist(ServiceBaseError):
    """Raised in case when product with received id does not exist."""


class OrderService(BaseService):
    """Service is responsible for working with the Order entity."""

    model = Order
    db_session: Session

    def _get_ordered_products(
        self, order_items: list[OrderItemSchema]
    ) -> list[Product]:
        received_product_ids = {item.product_id for item in order_items}
        query = select(Product).where(Product.id.in_(received_product_ids))
        products = self.db_session.scalars(query).all()

        if len(received_product_ids) != len(products):
            found_product_ids = [product.id for product in products]
            wrong_product_ids = received_product_ids.difference(found_product_ids)
            raise ProductDoesNotExist(
                message=f"Products with ids '{wrong_product_ids}' do not exist."
            )

        return products

    def create_order(
        self, user: User, order_data: OrderCreateSchema, delivery_address: Address
    ) -> Order:
        products = self._get_ordered_products(order_data.order_items)
        order_instance = self._create_order_instance(order_data, delivery_address)
        self._add_order_items_to_order(order_instance, products, order_data.order_items)
        user.orders.append(order_instance)

        self.db_session.flush()
        return order_instance

    def _add_order_items_to_order(
        self,
        order: Order,
        ordered_products: list[Product],
        order_items_data: list[OrderItemSchema],
    ):
        for product, order_item_data in zip(
            sorted(ordered_products, key=lambda x: x.id),
            sorted(order_items_data, key=lambda x: x.product_id),
        ):
            order_item = self._create_order_item_instance(product, order_item_data)
            order.order_items.append(order_item)

    def _create_order_instance(
        self, order_data: OrderCreateSchema, delivery_address: Address
    ) -> Order:
        return Order(comments=order_data.comments, address_id=delivery_address.id)

    def _create_order_item_instance(
        self, product: Product, order_item_data: OrderItemSchema
    ):
        return OrderItem(
            product_id=order_item_data.product_id,
            quantity=order_item_data.quantity,
            product_price=product.price,
        )

    def _prepare_read_all_query(
        self, query: Select, sort: str | None, filters: FilterData
    ) -> Select:
        total_price_subquery = self._create_order_total_price_subquery()
        query = query.join(
            total_price_subquery,
            self.model.id == total_price_subquery.c.order_id,
        ).add_columns(getattr(total_price_subquery.c, TOTAL_PRICE_FIELD))
        return super()._prepare_read_all_query(query, sort, filters)

    def _get_filtered_query(self, query: Select, filters: FilterData) -> Select:
        if user_id := filters.get("user_id", None):
            query = query.where(self.model.user_id == user_id)

        return super()._get_filtered_query(query, filters)

    def _create_order_total_price_subquery(self) -> Subquery:
        """Create and return subquery to calculate total order price.

        Returns:
            Subquery: SQLAlchemy Subquery object
        """
        return (
            select(
                OrderItem.order_id,
                func.sum(OrderItem.product_price * OrderItem.quantity).label(
                    TOTAL_PRICE_FIELD
                ),
            )
            .group_by(OrderItem.order_id)
            .subquery()
        )

    def _apply_sorting(self, query: Select, sort: str) -> Select:
        """Apply sorting to the given query based on the provided sort parameter."""
        sort_field = sort.lstrip("-")

        if sort.startswith("-"):
            return query.order_by(text(f"{sort_field} DESC"))
        else:
            return query.order_by(text(sort_field))

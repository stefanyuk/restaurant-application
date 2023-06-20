from sqlalchemy import select
from sqlalchemy.orm import Session

from src.apis.common_errors import ServiceBaseError
from src.apis.services.base import BaseService
from src.database.models import Order, OrderItem, Product, User, Address
from src.apis.users.schemas import OrderCreate, OrderItemData


class ProductDoesNotExist(ServiceBaseError):
    """Raised in case when product with received id does not exist."""


class OrderService(BaseService):
    """Service is responsible for working with the Order entity."""

    model = Order
    db_session: Session

    def _get_ordered_products(self, order_items: list[OrderItemData]) -> list[Product]:
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
        self, user: User, order_data: OrderCreate, delivery_address: Address
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
        order_items_data: list[OrderItemData],
    ):
        for product, order_item_data in zip(
            sorted(ordered_products, key=lambda x: x.id),
            sorted(order_items_data, key=lambda x: x.product_id),
        ):
            order_item = self._create_order_item_instance(product, order_item_data)
            order.order_items.append(order_item)

    def _create_order_instance(
        self, order_data: OrderCreate, delivery_address: Address
    ) -> Order:
        return Order(comments=order_data.comments, address_id=delivery_address.id)

    def _create_order_item_instance(
        self, product: Product, order_item_data: OrderItemData
    ):
        return OrderItem(
            product_id=order_item_data.product_id,
            quantity=order_item_data.quantity,
            product_price=product.price,
        )

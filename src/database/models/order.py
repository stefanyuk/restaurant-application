from enum import Enum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import Base
from src.database.models.types import timestamp


class OrderStatus(Enum):
    AWAITING = "AWAITING"
    DELIVERED = "DELIVERED"
    IN_DELIVERY = "IN DELIVERY"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[OrderStatus] = mapped_column(
        nullable=False, server_default=OrderStatus.AWAITING.name
    )
    ordered_at: Mapped[timestamp]
    comments: Mapped[str]
    user: Mapped["User"] = relationship(back_populates="orders")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    order_items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete",
        passive_deletes=True,
        lazy="selectin",
    )
    address_id: Mapped[int] = mapped_column(
        ForeignKey("addresses.id", ondelete="SET NULL"), nullable=False
    )
    delivery_address: Mapped["Address"] = relationship(
        back_populates="orders", lazy="selectin"
    )

    SORTABLE_FIELDS = {"total_price"}

    @property
    def total_price(self):
        return sum([item.product_price * item.quantity for item in self.order_items])

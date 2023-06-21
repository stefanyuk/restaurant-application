from sqlalchemy import ForeignKey, UniqueConstraint, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order: Mapped["Order"] = relationship(back_populates="order_items")
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    product: Mapped["Product"] = relationship(back_populates="order_items")
    quantity: Mapped[int] = mapped_column(nullable=False)
    product_price: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint("order_id", "product_id", name="order_product_uc"),
    )

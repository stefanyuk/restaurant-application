from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import Base
from src.database.models.constants import MAX_PRODUCT_NAME_LENGTH


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(MAX_PRODUCT_NAME_LENGTH), unique=True, nullable=False
    )
    summary: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    image_file: Mapped[Optional[str]] = mapped_column(nullable=True)
    category: Mapped["Category"] = relationship(back_populates="products")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=False
    )

    SEARCHABLE_FIELDS = {"name"}
    SORTABLE_FIELDS = {"name", "price"}

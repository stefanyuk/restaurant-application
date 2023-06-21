from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import Base
from src.database.models.constants import MAX_CATEGORY_NAME_LENGTH


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(MAX_CATEGORY_NAME_LENGTH), unique=True, nullable=False
    )
    products: Mapped[list["Product"]] = relationship(back_populates="category")

    SEARCHABLE_FIELDS = {"name"}
    SORTABLE_FIELDS = {"name"}

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import Base
from src.database.models.types import timestamp


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    city: Mapped[str] = mapped_column(nullable=False)
    street: Mapped[str] = mapped_column(nullable=False)
    street_number: Mapped[int] = mapped_column(nullable=False)
    postal_code: Mapped[str] = mapped_column(nullable=False)
    user: Mapped["User"] = relationship(back_populates="addresses")
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[timestamp]
    orders: Mapped[list["Order"]] = relationship(back_populates="delivery_address")

    @property
    def full_address(self):
        return f"{self.street}, {self.street_number}, {self.postal_code}, {self.city}"

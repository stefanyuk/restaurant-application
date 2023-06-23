from datetime import date
from typing import Optional

from passlib.context import CryptContext
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from src.database.models import Base
from src.database.models.constants import MAX_FIRST_NAME_LENGTH, MAX_LAST_NAME_LENGTH
from src.database.models.types import timestamp

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    first_name: Mapped[str] = mapped_column(String(MAX_FIRST_NAME_LENGTH))
    last_name: Mapped[str] = mapped_column(String(MAX_LAST_NAME_LENGTH))
    phone_number: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_admin: Mapped[bool] = mapped_column(server_default=expression.false())
    is_employee: Mapped[bool] = mapped_column(server_default=expression.false())
    registered_at: Mapped[timestamp]
    last_login_date: Mapped[timestamp]
    birth_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    addresses: Mapped[list["Address"]] = relationship(
        back_populates="user", cascade="all, delete", passive_deletes=True
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="user")
    employee_profile: Mapped["EmployeeProfile"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    SEARCHABLE_FIELDS = {"email", "first_name", "last_name", "phone_number"}
    SORTABLE_FIELDS = {"first_name", "last_name", "registered_at", "last_login_date"}

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = self._get_password_hash(password)

    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    def _get_password_hash(self, password):
        return pwd_context.hash(password)

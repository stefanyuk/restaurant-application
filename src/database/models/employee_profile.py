from sqlalchemy import ForeignKey, Numeric
from datetime import date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.models import Base


class EmployeeProfile(Base):
    __tablename__ = "employee_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    salary: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    available_holidays: Mapped[int]
    hire_date: Mapped[date] = mapped_column(nullable=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(back_populates="employee_profile")

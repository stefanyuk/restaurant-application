from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    SEARCHABLE_FIELDS: set[str]

    pass

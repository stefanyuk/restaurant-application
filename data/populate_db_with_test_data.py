import random
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


from api_tests.factories import (
    UserFactory,
    OrderFactory,
    AddressFactory,
    OrderItemFactory,
    ProductFactory,
    CategoryFactory,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base

engine = create_engine(
    "postgresql+psycopg2://postgres:postgres1234@localhost:5432/restaurant_db"
)
db_session = sessionmaker(engine)

ADMIN_USER_EMAIL = "admin@example.com"


def create_admin_user():
    user = UserFactory.create(email=ADMIN_USER_EMAIL, is_admin=True, is_employee=True)
    AddressFactory.create(user=user)

    return user


def create_categories():
    category_names = ("Bakery", "Coffee", "Tea")
    categories = []

    for category_name in category_names:
        categories.append(CategoryFactory.create(name=category_name))

    return categories


def create_products(categories):
    for _ in range(10):
        ProductFactory.create(category=random.choice(categories))


def main():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with db_session.begin() as ses:
        set_session_for_factories(ses)
        create_admin_user()
        categories = create_categories()
        create_products(categories)


def set_session_for_factories(db_session):
    UserFactory._meta.sqlalchemy_session = db_session
    AddressFactory._meta.sqlalchemy_session = db_session
    OrderFactory._meta.sqlalchemy_session = db_session
    OrderItemFactory._meta.sqlalchemy_session = db_session
    ProductFactory._meta.sqlalchemy_session = db_session
    CategoryFactory._meta.sqlalchemy_session = db_session


main()

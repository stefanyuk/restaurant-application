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
from src.database.models import User


engine = create_engine(
    "postgresql+psycopg2://postgres:postgres1234@localhost:5432/restaurant_db"
)
db_session = sessionmaker(engine)

ADMIN_USER_EMAIL = "admin@example.com"
ADMIN_USER_PASSWORD = "admin"


def print_progress_bar(
    iteration,
    total,
    prefix="",
    suffix="",
    decimals=1,
    length=100,
    fill="█",
    printEnd="\r",
):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + "-" * (length - filledLength)
    print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=printEnd)
    if iteration == total:
        print()


def create_admin_user():
    user = UserFactory.create(
        email=ADMIN_USER_EMAIL,
        is_admin=True,
        is_employee=True,
        password=ADMIN_USER_PASSWORD,
    )
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


def create_orders(user: User, order_amount: int = 10) -> None:
    for _ in range(order_amount):
        OrderFactory.create(user=user)


def create_user_with_address() -> User:
    user = UserFactory.create()
    AddressFactory.create(user=user)
    return user


def main():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    n = 20
    print_progress_bar(0, n, prefix="Progress:", suffix="Complete", length=100)

    with db_session.begin() as ses:
        set_session_for_factories(ses)
        categories = create_categories()
        create_products(categories)
        create_admin_user()

        for i in range(n):
            user = create_user_with_address()
            create_orders(user)
            print_progress_bar(
                i + 1, n, prefix="Progress:", suffix="Complete", length=100
            )


def set_session_for_factories(db_session):
    UserFactory._meta.sqlalchemy_session = db_session
    AddressFactory._meta.sqlalchemy_session = db_session
    OrderFactory._meta.sqlalchemy_session = db_session
    OrderItemFactory._meta.sqlalchemy_session = db_session
    ProductFactory._meta.sqlalchemy_session = db_session
    CategoryFactory._meta.sqlalchemy_session = db_session


main()

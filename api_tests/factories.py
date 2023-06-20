import factory
from factory.alchemy import SQLAlchemyModelFactory
from src.database.models import User, Address, Order, OrderItem, Product, Category


CURR_MODULE_PATH = "api_tests.factories"


class AddressFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Address
        sqlalchemy_session_persistence = "flush"

    city = factory.Faker("city")
    street = factory.Faker("street_name")
    street_number = factory.Faker("random_int", min=1)
    postal_code = factory.Faker("postcode")
    user = factory.SubFactory(f"{CURR_MODULE_PATH}.UserFactory")
    created_at = factory.Faker("date_time")


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "flush"

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password_hash = "password_hash"
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    phone_number = factory.Faker("phone_number")
    is_admin = False
    is_employee = False
    registered_at = factory.Faker("date_time")
    last_login_date = factory.Faker("date_time")
    birth_date = factory.Faker("date_of_birth")


class OrderFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Order
        sqlalchemy_session_persistence = "flush"

    status = "AWAITING"
    ordered_at = factory.Faker("date_time")
    comments = factory.Faker("text")
    user = factory.SubFactory(UserFactory)
    order_items = factory.RelatedFactoryList(
        f"{CURR_MODULE_PATH}.OrderItemFactory", "order", size=3
    )


class OrderItemFactory(SQLAlchemyModelFactory):
    class Meta:
        model = OrderItem
        sqlalchemy_session_persistence = "flush"

    product = factory.SubFactory(f"{CURR_MODULE_PATH}.ProductFactory")
    quantity = factory.Faker("random_int", min=1, max=10)
    product_price = factory.LazyAttribute(lambda obj: obj.product.price)


class ProductFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Product
        sqlalchemy_session_persistence = "flush"

    name = factory.Sequence(lambda n: f"Product {n}")
    summary = factory.Faker("text")
    price = factory.Faker("pydecimal", left_digits=4, right_digits=2, min_value=5)
    category = factory.SubFactory(f"{CURR_MODULE_PATH}.CategoryFactory")


class CategoryFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Category
        sqlalchemy_session_persistence = "flush"

    name = factory.Sequence(lambda n: f"Category {n}")

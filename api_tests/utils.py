from typing import Any, Mapping, Sequence
from datetime import datetime
from src.database.models import User
from src.apis.users.schemas import MIN_PASSWORD_LENGTH

ResponseData = Mapping[str, Any]
ExpectedData = Mapping[str, Any]


def assert_offset_limit_pagination_data(
    response_data: ResponseData,
    expected_items_len: int,
    expected_offset: int,
    expected_limit: int,
    expected_total: int,
):
    """Assert pagination information is as expected.

    Args:
        response_data (ResponseData): data received by API
        expected_items_len (int): expected number of entities received
        expected_offset (int): expected pagination offset
        expected_limit (int): expected pagination limit
        expected_total (int): expected total entities number
    """
    assert expected_offset == response_data["offset"]
    assert expected_limit == response_data["limit"]
    assert expected_total == response_data["total"]
    assert expected_items_len == len(response_data["items"])


def prepare_extended_user_data(user: User, with_id: bool = True) -> dict[str, Any]:
    """Prepare extended user information in a dictionary representation.

    Args:
        user (User): user data of which must be converted to dict

    Returns:
        dict[str, Any]: extended user information
    """
    user_data = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "birth_date": datetime.strftime(user.birth_date, "%Y-%m-%d"),
        "is_admin": user.is_admin,
        "is_employee": user.is_employee,
    }

    if with_id:
        user_data["id"] = user.id

    return user_data


def prepare_base_user_data(user: User, with_id: bool = True) -> dict[str, Any]:
    """Prepare base user information in a dictionary representation.

    Args:
        user (User): user data of which must be converted to dict

    Returns:
        dict[str, Any]: user base information
    """
    user_data = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "birth_date": datetime.strftime(user.birth_date, "%Y-%m-%d"),
    }

    if with_id:
        user_data["id"] = user.id

    return user_data


def assert_order_data(
    response_data: ResponseData,
    expected_order_data: ExpectedData,
    check_id: bool = True,
):
    expected_attrs = ("comments", "order_items", "total_price")

    assert "order" in response_data, "Response data is not embedded."

    order_data = response_data["order"]

    assert "id" in order_data, "Attribute 'id' was not found in response."

    _assert_attrs(expected_attrs, order_data, expected_order_data)

    if check_id is True:
        assert expected_order_data["id"] == order_data["id"]


def assert_api_error(
    error_data: ResponseData, expected_error_message: str, expected_error_code: int
):
    """Assert returned error data by API is as expected."""
    assert "detail" in error_data, "Attribute 'detail' was not found in error response"

    actual_error_data = error_data["detail"]

    assert expected_error_message == actual_error_data["message"]
    assert expected_error_code == actual_error_data["code"]


def assert_basic_user_data(
    response_data: ResponseData,
    expected_user_data: ExpectedData,
    check_id: bool = True,
):
    expected_attrs = ("email", "first_name", "last_name", "birth_date", "phone_number")

    assert "user" in response_data, "Response data is not embedded."

    user_data = response_data["user"]

    assert "id" in user_data, "Attribute 'id' was not found in response."

    _assert_attrs(expected_attrs, user_data, expected_user_data)

    if check_id is True:
        assert expected_user_data["id"] == user_data["id"]


def _assert_attrs(
    expected_attributes: Sequence[str],
    response_data: ResponseData,
    expected_data: ExpectedData,
):
    for attr in expected_attributes:
        assert attr in response_data, f"Attribute '{attr}' was not found in response."
        assert expected_data[attr] == response_data[attr]


def assert_extended_user_data(
    response_data: ResponseData,
    expected_user_data: ExpectedData,
    check_id: bool = True,
):
    expected_attrs = (
        "email",
        "first_name",
        "last_name",
        "birth_date",
        "phone_number",
        "is_employee",
        "is_admin",
    )

    assert "user" in response_data, "Response data is not embedded."

    user_data = response_data["user"]

    assert "id" in user_data, "Attribute 'id' was not found in response."

    _assert_attrs(expected_attrs, user_data, expected_user_data)

    if check_id is True:
        assert expected_user_data["id"] == user_data["id"]


def assert_category_data(
    response_data: ResponseData,
    expected_category_data: ExpectedData,
    check_id: bool = True,
):
    expected_attrs = ("name",)

    assert "category" in response_data, "Response data is not embedded."

    category_data = response_data["category"]

    assert "id" in category_data, "Attribute 'id' was not found in response."

    _assert_attrs(expected_attrs, category_data, expected_category_data)

    if check_id is True:
        assert expected_category_data["id"] == category_data["id"]


def assert_product_data(
    response_data: ResponseData,
    expected_product_data: ExpectedData,
    check_id: bool = True,
):
    expected_attrs = ("name", "summary", "price", "category_id")

    assert "product" in response_data, "Response data is not embedded."

    product_data = response_data["product"]

    assert "id" in product_data, "Attribute 'id' was not found in response."

    _assert_attrs(expected_attrs, product_data, expected_product_data)

    if check_id is True:
        assert expected_product_data["id"] == product_data["id"]


def assert_address_data(
    response_data: ResponseData,
    expected_address_data: ExpectedData,
    check_id: bool = True,
):
    expected_attrs = ("city", "street", "street_number", "postal_code")

    assert "delivery_address" in response_data, "Response data is not embedded."

    address_data = response_data["delivery_address"]

    assert "id" in address_data, "Attribute 'id' was not found in response."

    _assert_attrs(expected_attrs, address_data, expected_address_data)

    if check_id is True:
        assert expected_address_data["id"] == address_data["id"]


def assert_orders_collection(
    response_data: list[ResponseData],
    expected_orders_data: list[ExpectedData],
    expected_address_data: ExpectedData,
):
    assert len(response_data) == len(
        expected_orders_data
    ), "Collections have different length."

    for expected_data, actual_data in zip(expected_orders_data, response_data):
        assert_order_data(actual_data, expected_data)
        assert_address_data(actual_data, expected_address_data)


def assert_product_collection(
    response_data: list[ResponseData],
    expected_products_data: list[ExpectedData],
):
    assert len(response_data) == len(
        expected_products_data
    ), "Collections have different length."

    for expected_data, actual_data in zip(expected_products_data, response_data):
        assert_product_data(actual_data, expected_data)


def assert_category_collection(
    response_data: list[ResponseData],
    expected_categories_data: list[ExpectedData],
):
    assert len(response_data) == len(
        expected_categories_data
    ), "Collections have different length."

    for expected_data, actual_data in zip(expected_categories_data, response_data):
        assert_category_data(actual_data, expected_data)


def assert_user_collection_data(
    response_data: list[ResponseData],
    expected_users_data: list[ExpectedData],
):
    assert len(response_data) == len(
        expected_users_data
    ), "Collections have different length."

    for expected_data, actual_data in zip(expected_users_data, response_data):
        assert_extended_user_data(actual_data, expected_data)


def create_wrong_user_payload(wrong_field_name: str, wrong_field_value: str):
    """Create and return user data with the given wrong field."""
    new_user_data = {
        "email": "test@example.com",
        "first_name": "test_user",
        "last_name": "test_user",
        "phone_number": "+48567863891",
        "birth_date": "1995-06-25",
        "password": MIN_PASSWORD_LENGTH * "a",
    }

    new_user_data[wrong_field_name] = wrong_field_value

    return new_user_data

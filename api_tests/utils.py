from typing import Any, Mapping, Sequence
from datetime import datetime
from src.database.models import User


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
        "id": user.id,
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
    expected_attrs = ("comments", "order_items", "delivery_address")

    assert "id" in response_data, "Attribute 'id' was not found in response."

    _assert_attrs(expected_attrs, response_data, expected_order_data)

    if check_id is True:
        assert expected_order_data["id"] == response_data["id"]


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

    assert "id" in response_data, "Attribute 'id' was not found in response."

    _assert_attrs(expected_attrs, response_data, expected_user_data)

    if check_id is True:
        assert expected_user_data["id"] == response_data["id"]


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

    assert "id" in response_data, "Attribute 'id' was not found in response."

    _assert_attrs(expected_attrs, response_data, expected_user_data)

    if check_id is True:
        assert expected_user_data["id"] == response_data["id"]

# type: ignore

from typing import Any
from fastapi.testclient import TestClient
from fastapi import status
import pytest
from src.app import app
from src.database.models import User
from api_tests.utils import (
    assert_offset_limit_pagination_data,
    prepare_extended_user_data,
    prepare_base_user_data,
    assert_order_data,
    assert_api_error,
    assert_basic_user_data,
    assert_extended_user_data,
    assert_address_data,
    assert_orders_collection,
    assert_user_collection_data,
)
from api_tests.factories import (
    UserFactory,
    AddressFactory,
    ProductFactory,
    OrderFactory,
)
from src.apis.services.email_service import fm
from src.settings import settings
from src.apis.users.schemas import MIN_PASSWORD_LENGTH
from src.apis.token_backend import create_jwt_token_backend
from src.database.models.constants import MAX_FIRST_NAME_LENGTH
from src.database.models.constants import MAX_LAST_NAME_LENGTH
from src.apis.constants import DEFAULT_LIMIT, DEFAULT_OFFSET
from src.database.models.order import OrderStatus


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


def test_get_users_list_returns_200_on_success(
    admin_user_client: TestClient, admin_user
):
    expected_users = [UserFactory.create() for _ in range(3)] + [admin_user]
    expected_users_data = []

    for user in expected_users:
        expected_users_data.append(prepare_extended_user_data(user))

    url = app.url_path_for("get_users_list_api")

    response = admin_user_client.get(url)
    response_json = response.json()

    assert "items" in response_json, "Paginated collection is not embedded."

    sorted_response_data = sorted(response_json["items"], key=lambda x: x["user"]["id"])
    sorted_expected_data = sorted(expected_users_data, key=lambda x: x["id"])

    assert response.status_code == status.HTTP_200_OK
    assert_user_collection_data(sorted_response_data, sorted_expected_data)
    assert_offset_limit_pagination_data(
        response_json,
        expected_items_len=len(expected_users),
        expected_offset=DEFAULT_OFFSET,
        expected_limit=DEFAULT_LIMIT,
        expected_total=len(expected_users),
    )


def test_get_auth_user_info_returns_200_on_success(
    basic_user_client: TestClient, basic_user: User
):
    expected_user_data = prepare_base_user_data(basic_user)
    url = app.url_path_for("get_authenticated_user_info")

    response = basic_user_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "delivery_address" in response.json()
    assert_basic_user_data(response.json(), expected_user_data)


def test_create_auth_user_address_returns_201_on_success(basic_user_client: TestClient):
    url = app.url_path_for("create_authenticated_user_address_api")
    address_data = AddressFactory.build()

    expected_address_data = {
        "city": address_data.city,
        "street": address_data.street,
        "street_number": address_data.street_number,
        "postal_code": address_data.postal_code,
    }

    response = basic_user_client.post(url, json=expected_address_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert_address_data(response.json(), expected_address_data, check_id=False)


def test_create_auth_user_order_returns_201_on_success(
    basic_user_client: TestClient, basic_user: User
):
    product = ProductFactory.create(price=10)
    address = AddressFactory.create(user=basic_user)
    delivery_address = {
        "city": address.city,
        "street": address.street,
        "street_number": address.street_number,
        "postal_code": address.postal_code,
    }
    order_data = {
        "comments": "some comments",
        "order_items": [{"product_id": product.id, "quantity": 10}],
    }
    expected_order_data = {
        **order_data,
        "total_price": float(product.price * order_data["order_items"][0]["quantity"]),
    }

    url = app.url_path_for("create_authenticated_user_order_api")

    response = basic_user_client.post(
        url, json={"order": order_data, "delivery_address": delivery_address}
    )
    response_json = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert_order_data(response_json, expected_order_data, check_id=False)
    assert_address_data(response_json, delivery_address, check_id=False)


def test_create_auth_user_order_returns_400_when_product_does_not_exist(
    basic_user_client: TestClient, basic_user: User
):
    address = AddressFactory.create(user=basic_user)
    wrong_product_id = 7
    delivery_address = {
        "city": address.city,
        "street": address.street,
        "street_number": address.street_number,
        "postal_code": address.postal_code,
    }
    order_data = {
        "comments": "some comments",
        "order_items": [{"product_id": wrong_product_id, "quantity": 10}],
    }
    url = app.url_path_for("create_authenticated_user_order_api")
    expected_error_message = f"Products with ids '{{{wrong_product_id}}}' do not exist."

    response = basic_user_client.post(
        url, json={"order": order_data, "delivery_address": delivery_address}
    )

    assert_api_error(
        response.json(),
        expected_error_message=expected_error_message,
        expected_error_code=status.HTTP_400_BAD_REQUEST,
    )


def test_create_auth_user_order_returns_422_when_duplicated_order_items_provided(
    basic_user_client: TestClient, basic_user: User
):
    product = ProductFactory.create()
    address = AddressFactory.create(user=basic_user)
    delivery_address = {
        "city": address.city,
        "street": address.street,
        "street_number": address.street_number,
        "postal_code": address.postal_code,
    }
    order_data = {
        "comments": "some comments",
        "order_items": [
            {"product_id": product.id, "quantity": 10},
            {"product_id": product.id, "quantity": 10},
        ],
    }
    url = app.url_path_for("create_authenticated_user_order_api")

    response = basic_user_client.post(
        url, json={"order": order_data, "delivery_address": delivery_address}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == "Order items must be unique."


def test_obtain_reset_password_email_returns_202_on_success(
    api_client: TestClient, basic_user: User
):
    url = app.url_path_for("obtain_reset_password_email")

    with fm.record_messages() as outbox:
        payload = {"email": basic_user.email}

        response = api_client.post(url, json=payload)

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert len(outbox) == 1
        assert outbox[0]["from"] == settings.mail_username
        assert outbox[0]["to"] == basic_user.email


def test_obtain_reset_password_email_returns_404_when_user_does_not_exist(
    api_client: TestClient,
):
    url = app.url_path_for("obtain_reset_password_email")
    user_email = "test@example.com"
    expected_error_message = f"User with email '{user_email}' does not exist."

    with fm.record_messages():
        payload = {"email": user_email}

        response = api_client.post(url, json=payload)

        assert_api_error(
            response.json(),
            expected_error_message=expected_error_message,
            expected_error_code=status.HTTP_404_NOT_FOUND,
        )


def test_obtain_reset_password_email_returns_422_when_provided_email_is_invalid(
    api_client: TestClient,
):
    url = app.url_path_for("obtain_reset_password_email")

    with fm.record_messages():
        payload = {"email": "wrong_email"}

        response = api_client.post(url, json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_reset_user_password_returns_400_when_reset_token_is_invalid(
    api_client: TestClient,
):
    url = app.url_path_for("reset_user_password")
    payload = {"password": "a" * MIN_PASSWORD_LENGTH, "token": "invalid-token"}
    expected_error_message = "The provided token is not valid."

    response = api_client.patch(url, json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert_api_error(
        response.json(),
        expected_error_message=expected_error_message,
        expected_error_code=status.HTTP_400_BAD_REQUEST,
    )


def test_reset_user_password_returns_422_when_provided_password_is_invalid(
    api_client: TestClient,
):
    url = app.url_path_for("reset_user_password")
    payload = {"password": "a" * (MIN_PASSWORD_LENGTH - 1), "token": "invalid-token"}

    response = api_client.patch(url, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_reset_user_password_returns_204_on_success(
    api_client: TestClient, basic_user: User
):
    url = app.url_path_for("reset_user_password")
    token_backend = create_jwt_token_backend()
    reset_token = token_backend.create_api_token_for_user(
        basic_user, settings.password_reset_token_lifetime
    )
    payload = {"password": "a" * MIN_PASSWORD_LENGTH, "token": reset_token}

    response = api_client.patch(url, json=payload)

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_create_user_returns_201_on_success(api_client: TestClient):
    url = app.url_path_for("create_user_api")
    new_user_data = {
        "email": "test@example.com",
        "first_name": "test_user",
        "last_name": "test_user",
        "phone_number": "+48567863891",
        "birth_date": "1995-06-25",
        "password": MIN_PASSWORD_LENGTH * "a",
    }

    response = api_client.post(url, json=new_user_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert_basic_user_data(response.json(), new_user_data, check_id=False)


@pytest.mark.parametrize(
    "wrong_user_data, expected_error_message",
    [
        (
            create_wrong_user_payload("email", "wrong_email"),
            "value is not a valid email address",
        ),
        (
            create_wrong_user_payload("password", (MIN_PASSWORD_LENGTH - 1) * "a"),
            f"ensure this value has at least {MIN_PASSWORD_LENGTH} characters",
        ),
        (
            create_wrong_user_payload("phone_number", "12345678910"),
            "Provided phone number is incorrect.",
        ),
        (
            create_wrong_user_payload("phone_number", "+48345678"),
            "Provided phone number is incorrect.",
        ),
        (
            create_wrong_user_payload("first_name", ""),
            "ensure this value has at least 1 characters",
        ),
        (
            create_wrong_user_payload("first_name", "a" * (MAX_FIRST_NAME_LENGTH + 1)),
            f"ensure this value has at most {MAX_FIRST_NAME_LENGTH} characters",
        ),
        (
            create_wrong_user_payload("last_name", ""),
            "ensure this value has at least 1 characters",
        ),
        (
            create_wrong_user_payload("last_name", "a" * (MAX_LAST_NAME_LENGTH + 1)),
            f"ensure this value has at most {MAX_LAST_NAME_LENGTH} characters",
        ),
        (
            create_wrong_user_payload("last_name", "      "),
            "Value cannot be empty.",
        ),
        (
            create_wrong_user_payload("first_name", "      "),
            "Value cannot be empty.",
        ),
    ],
)
def test_create_user_returns_422_when_payload_is_wrong(
    api_client: TestClient, wrong_user_data: dict[str, Any], expected_error_message: str
):
    url = app.url_path_for("create_user_api")

    response = api_client.post(url, json=wrong_user_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == expected_error_message


def test_create_user_returns_400_when_user_with_the_provided_email_already_exists(
    api_client: TestClient, admin_user: User
):
    expected_error_message = f"User with email '{admin_user.email}' already exists."
    url = app.url_path_for("create_user_api")
    new_user_data = {
        "email": admin_user.email,
        "first_name": "test_user",
        "last_name": "test_user",
        "phone_number": "+48567863891",
        "birth_date": "1995-06-25",
        "password": MIN_PASSWORD_LENGTH * "a",
    }

    response = api_client.post(url, json=new_user_data)

    assert_api_error(
        response.json(), expected_error_message, status.HTTP_400_BAD_REQUEST
    )


def test_update_authenticated_user_info_returns_200_on_success(
    basic_user_client: TestClient,
):
    url = app.url_path_for("update_authenticated_user_info")
    new_user_data = {
        "email": "new_user_email@example.com",
        "first_name": "test_user",
        "last_name": "test_user",
        "phone_number": None,
        "birth_date": "1995-06-25",
        "password": MIN_PASSWORD_LENGTH * "a",
    }

    response = basic_user_client.patch(url, json=new_user_data)

    assert response.status_code == status.HTTP_200_OK
    assert_basic_user_data(response.json(), new_user_data, check_id=False)


def test_update_authenticated_user_info_returns_400_when_user_with_the_provided_email_already_exists(
    basic_user_client: TestClient, admin_user: User
):
    url = app.url_path_for("update_authenticated_user_info")
    expected_error_message = f"User with email '{admin_user.email}' already exists."
    new_user_data = {
        "email": admin_user.email,
        "first_name": "test_user",
        "last_name": "test_user",
        "phone_number": "+48567863891",
        "birth_date": "1995-06-25",
        "password": MIN_PASSWORD_LENGTH * "a",
    }

    response = basic_user_client.patch(url, json=new_user_data)

    assert_api_error(
        response.json(), expected_error_message, status.HTTP_400_BAD_REQUEST
    )


def test_create_user_by_admin_returns_201_on_success(admin_user_client: TestClient):
    url = app.url_path_for("create_user_by_admin_api")
    new_user_data = {
        "email": "test@example.com",
        "first_name": "test_user",
        "last_name": "test_user",
        "phone_number": "+48567863891",
        "birth_date": "1995-06-25",
        "password": MIN_PASSWORD_LENGTH * "a",
        "is_employee": True,
        "is_admin": False,
    }

    response = admin_user_client.post(url, json=new_user_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert_extended_user_data(response.json(), new_user_data, check_id=False)


@pytest.mark.parametrize(
    "wrong_user_data, expected_error_message",
    [
        (
            create_wrong_user_payload("email", "wrong_email"),
            "value is not a valid email address",
        ),
        (
            create_wrong_user_payload("password", (MIN_PASSWORD_LENGTH - 1) * "a"),
            f"ensure this value has at least {MIN_PASSWORD_LENGTH} characters",
        ),
        (
            create_wrong_user_payload("phone_number", "12345678910"),
            "Provided phone number is incorrect.",
        ),
        (
            create_wrong_user_payload("phone_number", "+48345678"),
            "Provided phone number is incorrect.",
        ),
        (
            create_wrong_user_payload("first_name", ""),
            "ensure this value has at least 1 characters",
        ),
        (
            create_wrong_user_payload("last_name", ""),
            "ensure this value has at least 1 characters",
        ),
        (
            create_wrong_user_payload("last_name", "      "),
            "Value cannot be empty.",
        ),
        (
            create_wrong_user_payload("first_name", "      "),
            "Value cannot be empty.",
        ),
        (
            create_wrong_user_payload("is_admin", "not a boolean"),
            "value could not be parsed to a boolean",
        ),
        (
            create_wrong_user_payload("is_employee", "not a boolean"),
            "value could not be parsed to a boolean",
        ),
    ],
)
def test_create_user_by_admin_returns_422_when_payload_is_wrong(
    admin_user_client: TestClient,
    wrong_user_data: dict[str, Any],
    expected_error_message: str,
):
    url = app.url_path_for("create_user_by_admin_api")

    response = admin_user_client.post(url, json=wrong_user_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == expected_error_message


def test_create_user_by_admin_returns_400_when_user_with_the_provided_email_already_exists(
    admin_user_client: TestClient, basic_user: User
):
    expected_error_message = f"User with email '{basic_user.email}' already exists."
    url = app.url_path_for("create_user_by_admin_api")
    new_user_data = {
        "email": basic_user.email,
        "first_name": "test_user",
        "last_name": "test_user",
        "phone_number": "+48567863891",
        "birth_date": "1995-06-25",
        "password": MIN_PASSWORD_LENGTH * "a",
        "is_employee": True,
        "is_admin": False,
    }

    response = admin_user_client.post(url, json=new_user_data)

    assert_api_error(
        response.json(), expected_error_message, status.HTTP_400_BAD_REQUEST
    )


def test_get_user_returns_user_data(admin_user_client: TestClient, basic_user: User):
    url = app.url_path_for("get_user_api", user_id=basic_user.id)
    expected_user_data = prepare_extended_user_data(basic_user)

    response = admin_user_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert_extended_user_data(response.json(), expected_user_data, check_id=True)


def test_get_user_returns_400_when_user_with_the_provided_id_does_not_exist(
    admin_user_client: TestClient,
):
    wrong_id = 10
    url = app.url_path_for("get_user_api", user_id=wrong_id)
    expected_error_message = "User with the provided id was not found."

    response = admin_user_client.get(url)

    assert_api_error(
        response.json(),
        expected_error_message,
        expected_error_code=status.HTTP_404_NOT_FOUND,
    )


def test_delete_user_returns_204_on_delete(
    admin_user_client: TestClient, basic_user: User
):
    url = app.url_path_for("delete_user_api", user_id=basic_user.id)

    response = admin_user_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_user_is_idempotent(admin_user_client: TestClient):
    non_existing_user_id = 100
    url = app.url_path_for("delete_user_api", user_id=non_existing_user_id)

    response = admin_user_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_update_user_address_returns_200_on_successful_update(
    basic_user_client: TestClient, basic_user: User
):
    address = AddressFactory.create(user=basic_user)
    new_address_data = {"city": "New city", "street": "New street"}
    expected_address_data = {
        **new_address_data,
        "postal_code": address.postal_code,
        "street_number": address.street_number,
    }
    url = app.url_path_for("update_auth_user_address", address_id=address.id)

    response = basic_user_client.patch(url, json=new_address_data)

    assert response.status_code == status.HTTP_200_OK
    assert_address_data(response.json(), expected_address_data, check_id=False)


def test_update_user_address_returns_400_when_address_does_not_exist(
    basic_user_client: TestClient,
):
    address_id = 10
    expected_error_message = f"Address with id '{address_id}' does not exist."
    new_address_data = {"city": "New city"}
    url = app.url_path_for("update_auth_user_address", address_id=address_id)

    response = basic_user_client.patch(url, json=new_address_data)

    assert_api_error(
        response.json(), expected_error_message, status.HTTP_400_BAD_REQUEST
    )


def test_get_auth_user_orders_returns_200_on_success(
    basic_user_client: TestClient, basic_user: User
):
    address = AddressFactory.create(user=basic_user)
    expected_orders = [
        OrderFactory.create(user=basic_user, delivery_address=address) for _ in range(3)
    ]
    expected_orders_data = []
    expected_delivery_address = {
        "id": address.id,
        "city": address.city,
        "street": address.street,
        "street_number": address.street_number,
        "postal_code": address.postal_code,
    }

    for order in expected_orders:
        expected_orders_data.append(
            {
                "id": order.id,
                "user_id": basic_user.id,
                "status": OrderStatus.AWAITING.value,
                "ordered_at": order.ordered_at,
                "comments": order.comments,
                "order_items": [
                    {"product_id": item.product.id, "quantity": item.quantity}
                    for item in order.order_items
                ],
                "total_price": float(
                    sum(
                        item.product_price * item.quantity for item in order.order_items
                    )
                ),
            }
        )

    url = app.url_path_for("get_auth_user_orders")

    response = basic_user_client.get(url)
    response_json = response.json()

    assert "items" in response_json, "Collection response is not embedded."

    sorted_response_data = sorted(
        response_json["items"], key=lambda x: x["order"]["id"]
    )
    sorted_expected_data = sorted(expected_orders_data, key=lambda x: x["id"])

    assert response.status_code == status.HTTP_200_OK
    assert_orders_collection(
        sorted_response_data, sorted_expected_data, expected_delivery_address
    )
    assert_offset_limit_pagination_data(
        response_json,
        expected_items_len=len(expected_orders_data),
        expected_offset=DEFAULT_OFFSET,
        expected_limit=DEFAULT_LIMIT,
        expected_total=len(expected_orders_data),
    )


@pytest.mark.parametrize(
    "sort_field, reverse",
    (("-total_price", 1), ("total_price", 0)),
)
def test_get_auth_user_orders_returns_orders_in_required_order(
    basic_user_client: TestClient, basic_user: User, sort_field: str, reverse: int
):
    address = AddressFactory.create(user=basic_user)
    expected_orders = [
        OrderFactory.create(user=basic_user, delivery_address=address) for _ in range(3)
    ]
    expected_orders_data = []
    expected_delivery_address = {
        "id": address.id,
        "city": address.city,
        "street": address.street,
        "street_number": address.street_number,
        "postal_code": address.postal_code,
    }

    for order in expected_orders:
        expected_orders_data.append(
            {
                "id": order.id,
                "user_id": basic_user.id,
                "status": OrderStatus.AWAITING.value,
                "ordered_at": order.ordered_at,
                "comments": order.comments,
                "order_items": [
                    {"product_id": item.product.id, "quantity": item.quantity}
                    for item in order.order_items
                ],
                "total_price": float(
                    sum(
                        item.product_price * item.quantity for item in order.order_items
                    )
                ),
            }
        )

    url = app.url_path_for("get_auth_user_orders")

    response = basic_user_client.get(url, params={"sort": sort_field})
    response_json = response.json()

    assert "items" in response_json, "Collection response is not embedded."

    sorted_expected_data = sorted(
        expected_orders_data, key=lambda x: x["total_price"], reverse=reverse
    )

    assert response.status_code == status.HTTP_200_OK
    assert_orders_collection(
        response_json["items"], sorted_expected_data, expected_delivery_address
    )
    assert_offset_limit_pagination_data(
        response_json,
        expected_items_len=len(expected_orders_data),
        expected_offset=DEFAULT_OFFSET,
        expected_limit=DEFAULT_LIMIT,
        expected_total=len(expected_orders_data),
    )


def test_get_auth_user_orders_returns_422_when_wrong_sorting_parameter_provided(
    basic_user_client: TestClient,
):
    wrong_sorting_field = "-wrong_field"
    expected_error_message = (
        f"Value '{wrong_sorting_field}' is "
        + "not in the list of allowed fields to sort by."
    )
    url = app.url_path_for("get_auth_user_orders")
    response = basic_user_client.get(url, params={"sort": wrong_sorting_field})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == expected_error_message

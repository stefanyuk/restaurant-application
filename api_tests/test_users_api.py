from fastapi.testclient import TestClient
from fastapi import status
from src.app import app
from src.database.models import User
from api_tests.utils import (
    assert_offset_limit_pagination_data,
    prepare_extended_user_data,
    prepare_base_user_data,
    assert_order_data,
    assert_api_error,
)
from api_tests.factories import (
    UserFactory,
    AddressFactory,
    ProductFactory,
)


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

    assert response.status_code == status.HTTP_200_OK
    assert sorted(response_json["items"], key=lambda x: x["id"]) == sorted(
        expected_users_data, key=lambda x: x["id"]
    )
    assert_offset_limit_pagination_data(
        response_json,
        expected_items_len=len(expected_users),
        expected_offset=0,
        expected_limit=50,
        expected_total=len(expected_users),
    )


def test_get_auth_user_info_returns_200_on_success(
    basic_user_client: TestClient, basic_user: User
):
    expected_user_data = prepare_base_user_data(basic_user)
    url = app.url_path_for("get_authenticated_user_info")

    response = basic_user_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert expected_user_data == response.json()


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
    response_json = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in response_json
    assert response_json["city"] == expected_address_data["city"]
    assert response_json["street"] == expected_address_data["street"]
    assert response_json["street_number"] == expected_address_data["street_number"]
    assert response_json["postal_code"] == expected_address_data["postal_code"]


def test_create_auth_user_order_returns_201_on_success(
    basic_user_client: TestClient, basic_user: User
):
    product = ProductFactory.create()
    address = AddressFactory.create(user=basic_user)
    expected_order_data = {
        "comments": "some comments",
        "order_items": [{"product_id": product.id, "quantity": 10}],
        "delivery_address": {
            "city": address.city,
            "street": address.street,
            "street_number": address.street_number,
            "postal_code": address.postal_code,
        },
    }
    url = app.url_path_for("create_authenticated_user_order_api")

    response = basic_user_client.post(url, json=expected_order_data)
    response_json = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert_order_data(response_json, expected_order_data, check_id=False)


def test_create_auth_user_order_returns_400_when_product_does_not_exist(
    basic_user_client: TestClient, basic_user: User
):
    address = AddressFactory.create(user=basic_user)
    wrong_product_id = 7
    expected_order_data = {
        "comments": "some comments",
        "order_items": [{"product_id": wrong_product_id, "quantity": 10}],
        "delivery_address": {
            "city": address.city,
            "street": address.street,
            "street_number": address.street_number,
            "postal_code": address.postal_code,
        },
    }
    url = app.url_path_for("create_authenticated_user_order_api")
    expected_error_message = f"Products with ids '{{{wrong_product_id}}}' do not exist."

    response = basic_user_client.post(url, json=expected_order_data)

    assert_api_error(
        response.json(),
        expected_error_message=expected_error_message,
        expected_error_code=status.HTTP_400_BAD_REQUEST,
    )

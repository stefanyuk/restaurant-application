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
    assert_basic_user_data,
    assert_extended_user_data,
)
from api_tests.factories import (
    UserFactory,
    AddressFactory,
    ProductFactory,
)
from src.apis.services.email_service import fm
from src.settings import settings
from src.apis.users.schemas import MIN_PASSWORD_LENGTH
from src.apis.token_backend import create_jwt_token_backend


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


def test_obtain_reset_password_email_returns_400_when_user_does_not_exist(
    api_client: TestClient,
):
    url = app.url_path_for("obtain_reset_password_email")
    user_email = "test@example.com"
    expected_error_message = f"User with email '{user_email}' does not exist."

    with fm.record_messages():
        payload = {"email": user_email}

        response = api_client.post(url, json=payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert_api_error(
            response.json(),
            expected_error_message=expected_error_message,
            expected_error_code=status.HTTP_400_BAD_REQUEST,
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
        "phone_number": "+48567863891",
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

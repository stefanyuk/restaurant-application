from typing import Any
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from src.app import app
from api_tests.utils import assert_api_error
from src.settings import settings
from src.database.models import User
from src.apis.token_backend import create_jwt_token_backend
from api_tests.factories import UserFactory
from src.database.models.constants import MAX_FIRST_NAME_LENGTH
from src.database.models.constants import MAX_LAST_NAME_LENGTH
from src.apis.users.schemas import MIN_PASSWORD_LENGTH
from api_tests.utils import assert_basic_user_data, create_wrong_user_payload


@pytest.mark.parametrize(
    "endpoint_path, http_method",
    (
        (app.url_path_for("create_category_api"), "post"),
        (app.url_path_for("get_categories_list_api"), "get"),
        (app.url_path_for("delete_category_api", category_id=1), "delete"),
        (app.url_path_for("create_product_api"), "post"),
        (app.url_path_for("get_products_list_api"), "get"),
        (app.url_path_for("create_user_by_admin_api"), "post"),
        (app.url_path_for("get_users_list_api"), "get"),
        (app.url_path_for("get_user_api", user_id=1), "get"),
        (app.url_path_for("delete_user_api", user_id=1), "delete"),
    ),
)
def test_admin_endpoints_are_protected(
    basic_user_client: TestClient, endpoint_path: str, http_method: str
):
    expected_error_message = "Access denied."
    response = getattr(basic_user_client, http_method)(endpoint_path)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert_api_error(
        response.json(),
        expected_error_message=expected_error_message,
        expected_error_code=status.HTTP_403_FORBIDDEN,
    )


@pytest.mark.parametrize(
    "endpoint_path, http_method",
    (
        (app.url_path_for("get_authenticated_user_info"), "get"),
        (app.url_path_for("update_authenticated_user_info"), "patch"),
        (app.url_path_for("create_authenticated_user_address_api"), "post"),
        (app.url_path_for("create_authenticated_user_order_api"), "post"),
    ),
)
def test_authenticated_user_endpoints_return_403_with_non_auth_request(
    api_client: TestClient, endpoint_path: str, http_method: str
):
    expected_error_message = "Not authenticated."
    response = getattr(api_client, http_method)(endpoint_path)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert_api_error(
        response.json(),
        expected_error_message=expected_error_message,
        expected_error_code=status.HTTP_403_FORBIDDEN,
    )


@pytest.mark.parametrize(
    "endpoint_path, http_method",
    (
        (app.url_path_for("get_authenticated_user_info"), "get"),
        (app.url_path_for("update_authenticated_user_info"), "patch"),
        (app.url_path_for("create_authenticated_user_address_api"), "post"),
        (app.url_path_for("create_authenticated_user_order_api"), "post"),
    ),
)
def test_authenticated_user_endpoints_return_403_when_token_is_invalid(
    api_client: TestClient, endpoint_path: str, http_method: str
):
    expected_error_message = "Token is not valid."
    response = getattr(api_client, http_method)(
        endpoint_path, headers={"Authorization": "Bearer token"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert_api_error(
        response.json(),
        expected_error_message=expected_error_message,
        expected_error_code=status.HTTP_403_FORBIDDEN,
    )


def test_get_tokens_for_user_returns_tokens_pair(
    api_client: TestClient, basic_user: User
):
    url = app.url_path_for("get_tokens_for_user")

    response = api_client.post(url, json={"email": basic_user.email})
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response_json
    assert "refresh" in response_json


def test_get_tokens_for_user_returns_404_when_user_with_provided_email_was_not_found(
    api_client: TestClient,
):
    user_email = "wrong_email@example.com"
    expected_error_message = f"User with email '{user_email}' was not found."
    url = app.url_path_for("get_tokens_for_user")

    response = api_client.post(url, json={"email": user_email})

    assert_api_error(response.json(), expected_error_message, status.HTTP_404_NOT_FOUND)


def test_refresh_token_returns_new_access_token_on_success(
    api_client: TestClient, basic_user: User
):
    url = app.url_path_for("refresh_token")
    token_backend = create_jwt_token_backend()
    refresh_token = token_backend.create_api_token_for_user(
        basic_user, settings.refresh_token_lifetime
    )

    response = api_client.post(url, json={"refresh": refresh_token})

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.json()


def test_refresh_token_returns_401_when_token_is_invalid(api_client: TestClient):
    url = app.url_path_for("refresh_token")
    expected_error_message = "Refresh token is invalid"

    response = api_client.post(url, json={"refresh": "refresh_token"})

    assert_api_error(
        response.json(), expected_error_message, status.HTTP_401_UNAUTHORIZED
    )


def test_refresh_token_returns_404_when_user_from_token_payload_was_not_found(
    api_client: TestClient,
):
    url = app.url_path_for("refresh_token")
    expected_error_message = "User with id from payload was not found."
    user = UserFactory.build(id=10)
    token_backend = create_jwt_token_backend()
    refresh_token = token_backend.create_api_token_for_user(
        user, settings.refresh_token_lifetime
    )

    response = api_client.post(url, json={"refresh": refresh_token})

    assert_api_error(response.json(), expected_error_message, status.HTTP_404_NOT_FOUND)


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
    response_json = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert_basic_user_data(response_json, new_user_data, check_id=False)
    assert "tokens" in response_json, "Tokens were not found in response."
    assert (
        "access" in response_json["tokens"]
    ), "Access token was not found in response."
    assert (
        "refresh" in response_json["tokens"]
    ), "Refresh token was not found in response."


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

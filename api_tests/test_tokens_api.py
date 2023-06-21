# type: ignore

from src.settings import settings
from src.database.models import User
from fastapi.testclient import TestClient
from src.app import app
from fastapi import status
from api_tests.utils import assert_api_error
from src.apis.token_backend import create_jwt_token_backend
from api_tests.factories import UserFactory


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

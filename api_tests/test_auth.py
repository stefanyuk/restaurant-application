import pytest
from fastapi.testclient import TestClient
from fastapi import status
from src.app import app
from api_tests.utils import assert_api_error


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

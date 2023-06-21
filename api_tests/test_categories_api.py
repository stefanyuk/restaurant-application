# type: ignore

from typing import Any
from fastapi.testclient import TestClient
import pytest
from src.database.models.constants import MAX_CATEGORY_NAME_LENGTH
from src.app import app
from fastapi import status
from api_tests.utils import (
    assert_category_data,
    assert_api_error,
    assert_offset_limit_pagination_data,
)
from api_tests.factories import CategoryFactory
from src.apis.constants import DEFAULT_LIMIT, DEFAULT_OFFSET

ENDPOINTS = {
    "CREATE": app.url_path_for("create_category_api"),
    "LIST": app.url_path_for("get_categories_list_api"),
}


def test_create_category_returns_201_on_success(admin_user_client: TestClient):
    new_category_data = {"name": "a" * MAX_CATEGORY_NAME_LENGTH}

    response = admin_user_client.post(ENDPOINTS["CREATE"], json=new_category_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert_category_data(response.json(), new_category_data, check_id=False)


def test_create_category_returns_400_when_category_with_provided_name_exists(
    admin_user_client: TestClient,
):
    category = CategoryFactory.create()
    new_category_data = {"name": category.name}
    expected_error_message = f"Category with name '{category.name}' already exists."
    response = admin_user_client.post(ENDPOINTS["CREATE"], json=new_category_data)

    assert_api_error(
        response.json(),
        expected_error_message,
        expected_error_code=status.HTTP_400_BAD_REQUEST,
    )


@pytest.mark.parametrize(
    "wrong_category_data, expected_error_message",
    (
        ({"name": "       "}, "Value cannot be empty."),
        ({"name": ""}, "ensure this value has at least 1 characters"),
        (
            {"name": "a" * (MAX_CATEGORY_NAME_LENGTH + 1)},
            f"ensure this value has at most {MAX_CATEGORY_NAME_LENGTH} characters",
        ),
    ),
)
def test_create_category_returns_422_when_wrong_payload_provided(
    admin_user_client: TestClient,
    wrong_category_data: dict[str, Any],
    expected_error_message: str,
):
    response = admin_user_client.post(ENDPOINTS["CREATE"], json=wrong_category_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == expected_error_message


def test_get_categories_list_returns_200_on_success(admin_user_client: TestClient):
    expected_categories = [CategoryFactory.create() for _ in range(3)]
    expected_categories_data = []

    for category in expected_categories:
        expected_categories_data.append({"id": category.id, "name": category.name})

    response = admin_user_client.get(ENDPOINTS["LIST"])
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert sorted(response_json["items"], key=lambda x: x["id"]) == sorted(
        expected_categories_data, key=lambda x: x["id"]
    )
    assert_offset_limit_pagination_data(
        response_json,
        expected_items_len=len(expected_categories),
        expected_offset=DEFAULT_OFFSET,
        expected_limit=DEFAULT_LIMIT,
        expected_total=len(expected_categories),
    )


def test_get_categories_list_returns_200_when_pagination_parameters_provided(
    admin_user_client: TestClient,
):
    limit = 2
    offset = 1
    categories = [CategoryFactory.create() for _ in range(3)]
    expected_categories_data = []

    for category in categories[offset:]:
        expected_categories_data.append({"id": category.id, "name": category.name})

    response = admin_user_client.get(
        ENDPOINTS["LIST"], params={"limit": limit, "offset": offset}
    )
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert sorted(response_json["items"], key=lambda x: x["id"]) == sorted(
        expected_categories_data, key=lambda x: x["id"]
    )
    assert_offset_limit_pagination_data(
        response_json,
        expected_items_len=len(expected_categories_data),
        expected_offset=offset,
        expected_limit=limit,
        expected_total=len(categories),
    )


@pytest.mark.parametrize("searched_pattern", ("CATEGORY", "CaTeGoRY", "category"))
def test_get_categories_list_returns_200_when_search_parameter_provided(
    admin_user_client: TestClient, searched_pattern: str
):
    [CategoryFactory.create(name=f"Some name {i}") for i in range(3)]
    categories_to_be_found = [
        CategoryFactory.create(name=f"Category {i}") for i in range(3)
    ]
    expected_categories_data = []

    for category in categories_to_be_found:
        expected_categories_data.append({"id": category.id, "name": category.name})

    response = admin_user_client.get(
        ENDPOINTS["LIST"], params={"search": searched_pattern}
    )
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert sorted(response_json["items"], key=lambda x: x["id"]) == sorted(
        expected_categories_data, key=lambda x: x["id"]
    )
    assert_offset_limit_pagination_data(
        response_json,
        expected_items_len=len(expected_categories_data),
        expected_offset=DEFAULT_OFFSET,
        expected_limit=DEFAULT_LIMIT,
        expected_total=len(expected_categories_data),
    )


def test_delete_category_returns_204_on_delete(admin_user_client: TestClient):
    category = CategoryFactory.create()
    url = app.url_path_for("delete_category_api", category_id=category.id)

    response = admin_user_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_category_is_idempotent(admin_user_client: TestClient):
    url = app.url_path_for("delete_category_api", category_id=10)

    response = admin_user_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_category_returns_422_when_provided_wrong_category_id(
    admin_user_client: TestClient,
):
    expected_error_message = "ensure this value is greater than 0"
    url = app.url_path_for("delete_category_api", category_id=0)

    response = admin_user_client.delete(url)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == expected_error_message

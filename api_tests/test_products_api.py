# type: ignore

from fastapi.testclient import TestClient
import pytest
from src.database.models.constants import MAX_PRODUCT_NAME_LENGTH
from src.app import app
from fastapi import status
from api_tests.utils import (
    assert_product_data,
    assert_api_error,
    assert_offset_limit_pagination_data,
    assert_product_collection,
)
from api_tests.factories import ProductFactory, CategoryFactory
from src.apis.constants import DEFAULT_LIMIT, DEFAULT_OFFSET


ENDPOINTS = {
    "CREATE": app.url_path_for("create_product_api"),
    "LIST": app.url_path_for("get_products_list_api"),
}


def create_wrong_product_payload(wrong_field_name: str, wrong_field_value: str):
    """Create and return product data with a given wrong field."""
    category = CategoryFactory.create()

    new_product_data = {
        "name": "a" * MAX_PRODUCT_NAME_LENGTH,
        "summary": "New product",
        "price": 10.90,
        "category_id": category.id,
    }

    new_product_data[wrong_field_name] = wrong_field_value

    return new_product_data


def test_create_product_returns_201_on_success(admin_user_client: TestClient):
    category = CategoryFactory.create()
    new_product_data = {
        "name": "a" * MAX_PRODUCT_NAME_LENGTH,
        "summary": "New product",
        "price": 10.90,
        "category_id": category.id,
    }

    response = admin_user_client.post(ENDPOINTS["CREATE"], json=new_product_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert_product_data(response.json(), new_product_data, check_id=False)


def test_create_product_returns_400_when_category_does_not_exist(
    admin_user_client: TestClient,
):
    expected_error_message = "Category with the provided id was not found."
    new_product_data = {
        "name": "a" * MAX_PRODUCT_NAME_LENGTH,
        "summary": "New product",
        "price": 10.90,
        "category_id": 10,
    }

    response = admin_user_client.post(ENDPOINTS["CREATE"], json=new_product_data)

    assert_api_error(
        response.json(),
        expected_error_message=expected_error_message,
        expected_error_code=status.HTTP_400_BAD_REQUEST,
    )


def test_create_product_returns_400_when_product_already_exists(
    admin_user_client: TestClient,
):
    product = ProductFactory.create()
    category = CategoryFactory.create()
    expected_error_message = f"Product with name '{product.name}' already exists."
    new_product_data = {
        "name": product.name,
        "summary": "New product",
        "price": 10.90,
        "category_id": category.id,
    }

    response = admin_user_client.post(ENDPOINTS["CREATE"], json=new_product_data)

    assert_api_error(
        response.json(),
        expected_error_message=expected_error_message,
        expected_error_code=status.HTTP_400_BAD_REQUEST,
    )


@pytest.mark.parametrize(
    "field_name, field_value, expected_error_message",
    (
        ("name", "    ", "Value cannot be empty."),
        ("name", "", "ensure this value has at least 1 characters"),
        (
            "name",
            "a" * (MAX_PRODUCT_NAME_LENGTH + 1),
            f"ensure this value has at most {MAX_PRODUCT_NAME_LENGTH} characters",
        ),
        ("category_id", 0, "ensure this value is greater than or equal to 1"),
        ("price", 0, "ensure this value is greater than or equal to 0.01"),
        ("price", 0.999, "ensure that there are no more than 2 decimal places"),
    ),
)
def test_create_product_returns_422_when_wrong_payload_provided(
    admin_user_client: TestClient,
    field_name: str,
    field_value: str,
    expected_error_message: str,
):
    product_payload = create_wrong_product_payload(field_name, field_value)
    response = admin_user_client.post(ENDPOINTS["CREATE"], json=product_payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == expected_error_message


def test_get_products_list_returns_200_on_success(admin_user_client: TestClient):
    expected_products = [ProductFactory.create() for _ in range(3)]
    expected_products_data = []

    for product in expected_products:
        expected_products_data.append(
            {
                "id": product.id,
                "name": product.name,
                "summary": product.summary,
                "price": float(product.price),
                "category_id": product.category_id,
            }
        )

    response = admin_user_client.get(ENDPOINTS["LIST"])
    response_json = response.json()

    assert "items" in response_json, "Paginated collection is not embedded."

    sorted_response_data = sorted(
        response_json["items"], key=lambda x: x["product"]["id"]
    )
    sorted_expected_data = sorted(expected_products_data, key=lambda x: x["id"])

    assert response.status_code == status.HTTP_200_OK
    assert_product_collection(sorted_response_data, sorted_expected_data)
    assert_offset_limit_pagination_data(
        response_json,
        expected_items_len=len(expected_products),
        expected_offset=DEFAULT_OFFSET,
        expected_limit=DEFAULT_LIMIT,
        expected_total=len(expected_products),
    )


def test_get_products_list_returns_200_when_pagination_parameters_provided(
    admin_user_client: TestClient,
):
    limit = 2
    offset = 1
    products = [ProductFactory.create() for _ in range(3)]
    expected_products_data = []

    for product in products[offset:]:
        expected_products_data.append(
            {
                "id": product.id,
                "name": product.name,
                "summary": product.summary,
                "price": float(product.price),
                "category_id": product.category_id,
            }
        )

    response = admin_user_client.get(
        ENDPOINTS["LIST"], params={"limit": limit, "offset": offset}
    )
    response_json = response.json()

    assert "items" in response_json, "Paginated collection is not embedded."

    sorted_response_data = sorted(
        response_json["items"], key=lambda x: x["product"]["id"]
    )
    sorted_expected_data = sorted(expected_products_data, key=lambda x: x["id"])

    assert response.status_code == status.HTTP_200_OK
    assert_product_collection(sorted_response_data, sorted_expected_data)
    assert_offset_limit_pagination_data(
        response_json,
        expected_items_len=len(expected_products_data),
        expected_offset=offset,
        expected_limit=limit,
        expected_total=len(products),
    )


def test_get_products_list_returns_422_when_wrong_sorting_parameter_provided(
    admin_user_client: TestClient,
):
    wrong_sorting_field = "-wrong_field"
    expected_error_message = (
        f"Value '{wrong_sorting_field}' is "
        + "not in the list of allowed fields to sort by."
    )
    response = admin_user_client.get(
        ENDPOINTS["LIST"], params={"sort": wrong_sorting_field}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == expected_error_message


@pytest.mark.parametrize(
    "sort_field, reverse",
    (
        ("-name", 1),
        ("name", 0),
        ("-price", 1),
        ("price", 0),
    ),
)
def test_get_products_list_returns_products_in_required_order(
    admin_user_client: TestClient, sort_field: str, reverse: int
):
    field = sort_field.lstrip("-")
    expected_products = [ProductFactory.create() for _ in range(3)]
    expected_products_data = []

    for product in expected_products:
        expected_products_data.append(
            {
                "id": product.id,
                "name": product.name,
                "summary": product.summary,
                "price": float(product.price),
                "category_id": product.category_id,
            }
        )
    expected_products_data = sorted(
        expected_products_data, key=lambda x: x[field], reverse=reverse
    )

    response = admin_user_client.get(ENDPOINTS["LIST"], params={"sort": sort_field})
    response_json = response.json()

    assert "items" in response_json, "Paginated collection is not embedded."

    response_data = response_json["items"]

    assert response.status_code == status.HTTP_200_OK
    assert_product_collection(response_data, expected_products_data)
    assert_offset_limit_pagination_data(
        response_json,
        expected_items_len=len(expected_products),
        expected_offset=DEFAULT_OFFSET,
        expected_limit=DEFAULT_LIMIT,
        expected_total=len(expected_products),
    )


def test_delete_product_returns_204_on_delete(admin_user_client: TestClient):
    product = ProductFactory.create()
    url = app.url_path_for("delete_product_api", product_id=product.id)

    response = admin_user_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_product_is_idempotent(admin_user_client: TestClient):
    url = app.url_path_for("delete_product_api", product_id=10)

    response = admin_user_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_product_returns_422_when_provided_wrong_product_id(
    admin_user_client: TestClient,
):
    expected_error_message = "ensure this value is greater than 0"
    url = app.url_path_for("delete_product_api", product_id=0)

    response = admin_user_client.delete(url)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == expected_error_message

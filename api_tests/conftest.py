import pytest
import os
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.apis.token_backend import JWTTokenBackend
from jose import jwt
from src.database.db import get_db_session
from src.database.models import Base, User
from sqlalchemy_utils import database_exists, create_database
from api_tests.factories import (
    UserFactory,
    AddressFactory,
    OrderFactory,
    OrderItemFactory,
    ProductFactory,
    CategoryFactory,
)
from src.settings import settings

SQLALCHEMY_TEST_DATABASE_URL = settings.test_db_connection_string

engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(autocommit=False, bind=engine)

if not database_exists(engine.url):
    create_database(engine.url)


def pytest_configure():
    os.environ["SUPPRESS_SEND"] = "1"


def pytest_unconfigure():
    os.environ["SUPPRESS_SEND"] = "0"


@pytest.fixture
def db_session():
    with TestingSessionLocal.begin() as session:
        yield session


@pytest.fixture
def application(db_session):
    from src.app import app

    app.dependency_overrides[get_db_session] = lambda: db_session

    return app


@pytest.fixture
def admin_user():
    return UserFactory.create(is_admin=True, is_employee=True)


@pytest.fixture
def basic_user():
    return UserFactory.create(is_admin=False, is_employee=False)


@pytest.fixture
def api_client(application: FastAPI):
    with TestClient(app=application, base_url="http://test") as client:
        yield client


@pytest.fixture
def basic_user_client(application: FastAPI, basic_user: User):
    with TestClient(app=application, base_url="http://test") as client:
        access_token = JWTTokenBackend(jwt).create_api_token_for_user(
            basic_user, settings.access_token_lifetime
        )
        client.headers = {"Authorization": f"Bearer {access_token}"}
        yield client


@pytest.fixture
def admin_user_client(application: FastAPI, admin_user: User):
    with TestClient(app=application) as client:
        access_token = JWTTokenBackend(jwt).create_api_token_for_user(
            admin_user, settings.access_token_lifetime
        )
        client.headers = {"Authorization": f"Bearer {access_token}"}
        yield client


@pytest.fixture(autouse=True)
def create_all_tables():
    """Delete and recreate all tables."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def set_session_for_factories(db_session):
    UserFactory._meta.sqlalchemy_session = db_session
    AddressFactory._meta.sqlalchemy_session = db_session
    OrderFactory._meta.sqlalchemy_session = db_session
    OrderItemFactory._meta.sqlalchemy_session = db_session
    ProductFactory._meta.sqlalchemy_session = db_session
    CategoryFactory._meta.sqlalchemy_session = db_session

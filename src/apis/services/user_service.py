from datetime import datetime
from typing import Optional
from sqlalchemy import and_, select

from sqlalchemy.orm import Session

from src.apis.common_errors import ServiceBaseError
from src.apis.services.base import BaseService, DataObject
from src.apis.users.schemas import UserCreate, AddressSchema
from src.database.models import User, Address


class UserAlreadyExists(ServiceBaseError):
    """Raised when user already exists."""


class UserDoesNotExist(ServiceBaseError):
    """Raised in case when user with received id does not exist."""


class UserService(BaseService):
    """Service is responsible for working with the User entity."""

    model = User
    db_session: Session
    _entity_not_found_error = UserDoesNotExist(
        message="User with the provided id was not found."
    )

    def _check_if_user_exists(self, email: str) -> None:
        user = self.get_by_field_value("email", email)

        if user is not None:
            raise UserAlreadyExists(
                message=f"User with email '{email}' already exists."
            )

    def create_user(self, user_data: UserCreate) -> User:
        """Create and persist new user.

        Args:
            user_data (UserCreate): new user data

        Returns:
            User: new user instance

        Raises:
            UserAlreadyExists: in case when user with provided email already exists
        """
        self._check_if_user_exists(user_data.email)
        return super()._create(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            password=user_data.password,
            phone_number=user_data.phone_number,
            birth_date=user_data.birth_date,
            is_admin=getattr(user_data, "is_admin", False),
            is_employee=getattr(user_data, "is_employee", False),
        )

    def update_user_last_login_date(
        self, user_id: int, new_last_login_time: datetime
    ) -> User:
        """Update last_login attribute value for the specified user.

        Args:
            user_id (int): unique user identifier
            new_last_login_time (datetime): time for last login update

        Returns:
            User: user entity with update last login time
        """
        user = self.get_by_id(user_id)

        return self.update(user, {"last_login_date": new_last_login_time})

    def update_user_data(self, user_id: int, new_user_data: DataObject) -> User:
        """Update data for the user with the provided id.

        Args:
            user_id (int): unique user identifier
            new_user_data (DataObject): data for user update, where key
            is the field name and value is the value to update

        Returns:
            User: updated user entity
        """
        if email := new_user_data.get("email", None):
            self._check_if_user_exists(email)

        user = self.get_by_id(user_id)

        return self.update(user, new_user_data)

    def _find_user_address(
        self,
        user: User,
        address_data: AddressSchema,
    ) -> Optional[Address]:
        filters = []

        for key, value in address_data:
            filters.append(getattr(Address, key) == value)

        query = (
            select(Address)
            .join(self.model)
            .where(and_(self.model.id == user.id, *filters))
        )

        return self.db_session.scalars(query).first()

    def add_address(self, user: User, address_data: AddressSchema) -> Address:
        """Add new user address.

        If user address already exists, function does not create a new one.

        Args:
            user (User): user for which address should be created
            address_data (AddressBase): new address data

        Returns:
            Address: created address entity
        """
        address = self._find_user_address(user, address_data)

        if address is not None:
            return address

        address = self._create_address_instance(address_data)
        user.addresses.append(address)
        self.db_session.flush()
        return address

    def _create_address_instance(self, address_data: AddressSchema) -> Address:
        return Address(
            city=address_data.city,
            street=address_data.street,
            street_number=address_data.street_number,
            postal_code=address_data.postal_code,
        )

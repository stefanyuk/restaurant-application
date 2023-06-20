import abc
from calendar import timegm
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Protocol

from jose.exceptions import JWTError

from src.apis.services.user_service import UserService, UserDoesNotExist
from src.database.models import User
from src.settings import settings

TokenPayload = Mapping[str, Any]


class InvalidToken(Exception):
    """Raised in case when API token is not valid."""

    pass


class TokenTypes(Enum):
    ACCESS = "ACCESS"
    REFRESH = "REFRESH"


class JWTBackendProtocol(Protocol):
    """JWT service implementation for API token operations."""

    def decode(
        self, token: str, shared_secret: str, algorithm: str
    ) -> Mapping[str, Any]:
        """Set decode token interface."""
        ...

    def encode(self, payload: TokenPayload, secret: str, algorithm: str) -> str:
        """Set encode token interface."""
        ...


class APITokenBackend(abc.ABC):
    """Base backend service implementation for API token operations."""

    _access_token_lifetime = settings.access_token_lifetime
    _refresh_token_lifetime = settings.refresh_token_lifetime
    _expiration_time_claim_name = settings.expiration_time_claim_name
    _issued_at_time_claim_name = settings.issued_at_time_claim_name
    _user_id_claim_name = settings.user_id_claim_name

    @abc.abstractmethod
    def create_api_token_for_user(self, user: User, token_type: TokenTypes) -> str:
        """Set create token interface for all subclasses."""
        pass

    @abc.abstractmethod
    def get_user_from_token(self, token: str, user_service: UserService) -> User:
        """Set get user from token interface for all subclasses."""
        pass

    @abc.abstractmethod
    def verify(self, token: str) -> TokenPayload:
        """Set verify token interface for all subclasses."""
        pass

    @abc.abstractmethod
    def __call__(self, *args: Any, **kwds: Any) -> "APITokenBackend":
        """Set __call__ interface for all subclasses."""
        pass


class JWTTokenBackend(APITokenBackend):
    """Backend service is responsible for API token operations."""

    def __init__(
        self,
        jwt_backend: JWTBackendProtocol,
        shared_secret: str = settings.secret_key,
        algorithm="HS256",
    ):
        self.jwt_backend = jwt_backend
        self.shared_secret = shared_secret
        self.algorithm = algorithm
        self._current_time = datetime.utcnow()

    def __call__(self) -> "JWTTokenBackend":
        return self

    def create_api_token_for_user(self, user: User, token_type: TokenTypes) -> str:
        """Create new API token for the given user."""
        payload = self._create_user_token_payload(user, token_type)
        return self.jwt_backend.encode(payload, self.shared_secret, self.algorithm)

    def get_user_from_token(self, token: str, user_service: UserService) -> User:
        """Return user instance with email given in token payload."""
        token_payload = self.verify(token)

        try:
            user = user_service.get_by_id(token_payload[self._user_id_claim_name])
        except UserDoesNotExist:
            raise InvalidToken

        return user

    def verify(self, token: str) -> TokenPayload:
        try:
            payload = self._decode_api_token(token)
            self._verify_payload_claims(payload)
            self._check_token_expiration_time(payload[self._expiration_time_claim_name])
        except (JWTError, KeyError):
            raise InvalidToken

        return payload

    def _decode_api_token(self, token: str) -> TokenPayload:
        try:
            payload = self.jwt_backend.decode(token, self.shared_secret, self.algorithm)
        except JWTError:
            raise InvalidToken

        return payload

    def _check_token_expiration_time(self, expiration_timestamp: int):
        expiration_time = datetime.fromtimestamp(expiration_timestamp)

        if self._current_time >= expiration_time:
            raise JWTError

    def _verify_payload_claims(self, payload: TokenPayload) -> None:
        """Verify whether payload contains required claims."""

        user_id = payload.get(self._user_id_claim_name)
        exp = payload.get(self._expiration_time_claim_name)
        iat = payload.get(self._issued_at_time_claim_name)

        if any(map(lambda x: x is None, (user_id, exp, iat))):
            raise KeyError("Invalid token claims.")

    def _create_user_token_payload(
        self, user: User, token_type: TokenTypes
    ) -> TokenPayload:
        if token_type == token_type.ACCESS:
            expiration_date = self._current_time + self._access_token_lifetime
        else:
            expiration_date = self._current_time + self._refresh_token_lifetime

        return {
            self._user_id_claim_name: user.id,
            self._issued_at_time_claim_name: self._convert_to_timestamp(
                self._current_time
            ),
            self._expiration_time_claim_name: self._convert_to_timestamp(
                expiration_date
            ),
        }

    def _convert_to_timestamp(self, date: datetime):
        return timegm(date.utctimetuple())

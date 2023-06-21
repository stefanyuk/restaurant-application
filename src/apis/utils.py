import phonenumbers
from phonenumbers import NumberParseException
from typing import Sequence


def check_phone_number(phone_number: str | None) -> str | None:
    """Validate whether provided phone number is correct.

    Args:
        phone_number (str | None): provided phone number value or None

    Raises:
        ValueError: in case when provided phone number is incorrect

    Returns:
        str: phone number
    """
    if phone_number is None:
        return phone_number

    is_valid = None

    try:
        number = phonenumbers.parse(phone_number)
        if not phonenumbers.is_valid_number(number):
            is_valid = False
    except NumberParseException:
        is_valid = False

    if is_valid is False:
        raise ValueError("Provided phone number is incorrect.")

    return phone_number


def check_if_value_is_not_empty(name: str):
    """Check if provided value is not empty after space removal.

    Args:
        name (str): name to be checked

    Raises:
        ValueError: in case if provided value is empty
    """
    name = name.strip()

    if name == "":
        raise ValueError("Value cannot be empty.")

    return name


def check_provided_sort_field(allowed_fields: Sequence[str], provided_sort_field: str):
    """Check if provided  sort field is in the list of allowed fields to be sorted by.

    Args:
        allowed_fields (Sequence[str]): allowed fields to be sorted by
        provided_sort_field (str): given sort field
    """
    if provided_sort_field is not None:
        field = provided_sort_field.lstrip("-")

        if field not in allowed_fields:
            raise ValueError(
                f"Value '{provided_sort_field}' is "
                + "not in the list of allowed fields to sort by."
            )

    return provided_sort_field

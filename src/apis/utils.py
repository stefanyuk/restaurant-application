import phonenumbers
from phonenumbers import NumberParseException


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

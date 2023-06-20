from typing import Protocol, TypeVar, Type
from src.database.models import User, Order
from pydantic import BaseModel
from fastapi_mail import MessageSchema, MessageType
from src.apis.token_backend import APITokenBackend
from src.settings import settings
from fastapi_mail import ConnectionConfig, FastMail


conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    SUPPRESS_SEND=settings.suppress_send,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    TEMPLATE_FOLDER=settings.base_templates_folder_path,
)

fm = FastMail(conf)


EmailMessageType = TypeVar("EmailMessageType", bound=BaseModel)


class EmailSender(Protocol):
    async def send_message(
        self, message: Type[EmailMessageType], template_name: str
    ) -> None:
        ...


async def send_order_creation_notification_email(
    recipient: User, order: Order, email_sender: EmailSender
) -> None:
    """Send order creation notification email to the given user.

    Args:
        recipient (User): email recipient
        order (Order): order that was created
    """
    template_body = {
        "user": recipient,
        "full_address": order.delivery_address.full_address,
        "order": order,
    }
    message = MessageSchema(
        subject="Order Confirmation",
        recipients=[recipient.email],
        template_body=template_body,
        subtype=MessageType.html,
    )

    await email_sender.send_message(message, template_name="order_created.html")


async def send_password_reset_email(
    recipient: User, token_backend: APITokenBackend, email_sender: EmailSender
) -> None:
    reset_token = token_backend.create_api_token_for_user(
        recipient, settings.password_reset_token_lifetime
    )
    reset_url = f"https://example.com/reset-password?token={reset_token}"
    template_body = {"user": recipient, "reset_url": reset_url}
    message = MessageSchema(
        subject="Password reset",
        recipients=[recipient.email],
        template_body=template_body,
        subtype=MessageType.html,
    )
    await email_sender.send_message(message, template_name="password_reset_email.html")

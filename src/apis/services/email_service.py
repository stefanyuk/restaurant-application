from src.database.models import User, Order, Address
from src.settings import settings

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType


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


async def send_order_creation_notification_email(
    recipient: User, order: Order, address: Address
) -> None:
    """Send order creation notification email to the given user.

    Args:
        recipient (User): email recipient
        order (Order): order that was created
    """
    template_body = {
        "user": recipient,
        "full_address": address.full_address,
        "order": order,
    }
    message = MessageSchema(
        subject="Order Confirmation.",
        recipients=[recipient.email],
        template_body=template_body,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)

    await fm.send_message(message, template_name="order_created.html")

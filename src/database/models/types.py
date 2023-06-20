from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import mapped_column
from typing_extensions import Annotated

timestamp = Annotated[
    datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]

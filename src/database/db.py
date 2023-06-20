from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.settings import settings

engine = create_engine(settings.db_connection_string, echo=True)
db_session = sessionmaker(engine)


def get_db_session() -> Session:
    """Create and yield an SQLAlchemy database session.

    The session will be automatically committed in case of successful
    processing of the request. Otherwise it will be rolledback.

    Yields:
        Iterator[Session]: SQLAlchemy session object
    """
    with db_session.begin() as session:
        yield session

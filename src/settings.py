from datetime import timedelta

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Class representing application settings."""

    api_v1_version_prefix: str = "/v1"
    host: str = Field("127.0.0.1")
    port: str = Field("8080")
    db_connection_string: str
    secret_key: str = "secret"
    access_token_lifetime: timedelta = timedelta(days=5)
    refresh_token_lifetime: timedelta = timedelta(days=1)
    password_reset_token_lifetime: timedelta = timedelta(minutes=5)
    expiration_time_claim_name: str = "exp"
    issued_at_time_claim_name: str = "iat"
    user_id_claim_name: str = "user_id"
    static_folder_path: str = "src/static/"
    debug: bool
    base_templates_folder_path: str = "src/templates"
    suppress_send: int = 1

    # Email conf
    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int = 587
    mail_server: str

    class Config:
        """Class representing Pydantic settings configuration."""

        env_file = ".env"


settings = Settings()

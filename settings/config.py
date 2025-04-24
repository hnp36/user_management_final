from builtins import bool, int, str
from pathlib import Path
from pydantic import Field, AnyUrl
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # General
    max_login_attempts: int = Field(default=3)

    # Server configuration
    server_base_url: AnyUrl = Field(default='http://localhost')
    server_download_folder: str = Field(default='downloads')

    # Security and authentication
    secret_key: str = Field(default="secret-key")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_minutes: int = Field(default=1440)
    admin_user: str = Field(default='admin')
    admin_password: str = Field(default='secret')
    debug: bool = Field(default=False)
    jwt_secret_key: str = "a_very_secret_key"
    jwt_algorithm: str = "HS256"

    # Database
    database_url: str = Field(default='postgresql+asyncpg://user:password@postgres/myappdb')
    postgres_user: str = Field(default='user')
    postgres_password: str = Field(default='password')
    postgres_server: str = Field(default='localhost')
    postgres_port: str = Field(default='5432')
    postgres_db: str = Field(default='myappdb')

    # Discord
    discord_bot_token: str = Field(default='NONE')
    discord_channel_id: int = Field(default=1234567890)

    # OpenAI
    openai_api_key: str = Field(default='NONE')

    # Email config
    send_real_mail: bool = Field(default=False)

    smtp_server: str = Field(default='sandbox.smtp.mailtrap.io')
    smtp_port: int = Field(default=587)
    smtp_username: str = Field(default='ccfa182face11a')
    smtp_password: str = Field(default='abf930a4e1c3d1')

    smtp_from: str = Field(default='no-reply@example.com', alias='smtp_FROM')
    smtp_from_name: str = Field(default='User Management App', alias='smtp_FROM_NAME')
    smtp_tls: bool = Field(default=True, alias='smtp_TLS')
    smtp_ssl: bool = Field(default=False, alias='smtp_SSL')

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "forbid"  # helps catch any typo in .env

# Instantiate settings
settings = Settings()

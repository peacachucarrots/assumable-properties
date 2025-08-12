from pydantic import SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ACCESS_TOKEN: SecretStr
    APP_SESSION_SECRET: SecretStr
    APP_SESSION_MAX_AGE: int = 7 * 24 * 60 * 60

    COOKIE_NAME: SecretStr

    class Config:
        env_file = ".env"

settings = Settings()
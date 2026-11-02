from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./orbitfin.db"
    # Sem valor padrão de propósito: o app se recusa a iniciar sem uma chave de verdade.
    secret_key: str = Field(min_length=32)
    access_token_expire_minutes: int = 30


settings = Settings()

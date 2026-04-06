from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_USERNAME: str = 'postgres'
    DB_PASSWORD: str = 'Romihay123!'
    DB_SERVER: str = '127.0.0.1'
    DB_PORT: str = '5432'
    DB_NAME: str = 'wolt'  # hamelia

    class Config:
        env_file = ".env"

settings = Settings()

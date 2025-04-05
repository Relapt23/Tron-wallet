import os


class DBConfig:
    HOST: str = os.getenv("DB_HOST")
    PORT: int = os.getenv("DB_PORT", 5432)
    USER: str = os.getenv("POSTGRES_USER")
    PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    DATABASE: str = os.getenv("POSTGRES_DB")

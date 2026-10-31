import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    PORT: int = int(os.getenv("PORT", "8002"))


settings = Settings()

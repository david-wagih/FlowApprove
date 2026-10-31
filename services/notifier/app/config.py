import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    FROM_ADDRESS: str = os.getenv("FROM_ADDRESS", "flowapprove@example.com")


settings = Settings()

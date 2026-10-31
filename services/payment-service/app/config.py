import os
from decimal import Decimal

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/payments_db"
    )
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    # How long the simulated bank transfer takes.
    PAYMENT_SECONDS: float = float(os.getenv("PAYMENT_SECONDS", "2"))
    # Share of payments that randomly fail (bank timeout), to have something real to monitor.
    PAYMENT_FAILURE_RATE: float = float(os.getenv("PAYMENT_FAILURE_RATE", "0.1"))
    # Anything above this is always declined — a deterministic way to see the failure path.
    PAYMENT_LIMIT: Decimal = Decimal(os.getenv("PAYMENT_LIMIT", "5000"))
    PORT: int = int(os.getenv("PORT", "8003"))


settings = Settings()

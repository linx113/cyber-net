import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = os.getenv(
    "LOG_DATABASE_URL",
    "postgresql+psycopg://cybernet:cybernet_dev@postgres-logs:5432/cybernet_logs"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=40,
    max_overflow=40,
    pool_timeout=5
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

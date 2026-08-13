from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_URL, DB_PATH


class Base(DeclarativeBase):
    pass


DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    from app import models  # noqa: F401 register models on Base before create_all

    Base.metadata.create_all(engine)


def get_session() -> Session:
    return SessionLocal()


def get_db():
    """FastAPI dependency: a request-scoped session that always closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

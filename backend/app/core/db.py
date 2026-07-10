from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

from app.core.config import settings

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)
Base = declarative_base(metadata=metadata)


def _engine_kwargs() -> dict:
    url = settings.DATABASE_URL
    kwargs: dict = {"echo": settings.DATABASE_ECHO, "future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs.update(
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return kwargs


engine = create_engine(settings.DATABASE_URL, **_engine_kwargs())

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

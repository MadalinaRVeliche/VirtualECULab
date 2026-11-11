import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

database_url = os.getenv("DATABASE_URL") or URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USER", "virtualeculab_app"),
    password=os.getenv("DB_PASSWORD", ""),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "virtualeculab"),
)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False}
    if str(database_url).startswith("sqlite")
    else {},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as session:
        yield session

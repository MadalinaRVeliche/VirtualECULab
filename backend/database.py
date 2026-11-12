import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Resolve .env relative to the repository so startup does not depend on
# the terminal's working directory. Existing environment variables take priority.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Render provides DATABASE_URL. For local development, build the URL
# from the individual DB_* settings in .env.
configured_url = os.getenv("DATABASE_URL")
database_url = (
    make_url(configured_url)
    if configured_url
    else URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER", "virtualeculab_app"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "virtualeculab"),
    )
)

# Hosting providers can supply a generic PostgreSQL URL. Select the psycopg
# driver installed by the project while preserving the URL's other settings.
if database_url.drivername in {"postgres", "postgresql"}:
    database_url = database_url.set(drivername="postgresql+psycopg")

# Check pooled connections before reuse in case the database closed one.
# The SQLite thread option applies only when the app is configured for SQLite.
engine = create_engine(
    database_url,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False}
    if str(database_url).startswith("sqlite")
    else {},
)

# Keep loaded model attributes available after commit so response builders
# can read fields such as a saved quiz session ID without another query.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    # FastAPI injects one session per request. The context manager closes it
    # afterward. The route decides when to commit its writes.
    with SessionLocal() as session:
        yield session
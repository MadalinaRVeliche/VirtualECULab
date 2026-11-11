"""Create additive learning tables. Never drop or alter existing progress tables."""

import argparse

from backend import models  # noqa: F401 - registers all model metadata
from backend.database import Base, engine

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Require the documented local PostgreSQL database.",
    )
    args = parser.parse_args()
    if args.local_only and not (
        engine.dialect.name == "postgresql"
        and engine.url.host in {"localhost", "127.0.0.1", "::1"}
        and engine.url.database == "virtualeculab"
    ):
        raise SystemExit(
            "Refusing setup: expected local PostgreSQL database virtualeculab. Check project .env and inherited DATABASE_URL without sharing credentials."
        )
    Base.metadata.create_all(bind=engine)
    print("Learning tables ready. Existing lesson progress is preserved.")

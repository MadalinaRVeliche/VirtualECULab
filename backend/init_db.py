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

    # The local setup command expects a loopback PostgreSQL connection
    # to the virtualeculab database. This catches a hosted DATABASE_URL
    # left in the environment before any tables are created.
    if args.local_only and not (
        engine.dialect.name == "postgresql"
        and engine.url.host in {"localhost", "127.0.0.1", "::1"}
        and engine.url.database == "virtualeculab"
    ):
        raise SystemExit(
            "Refusing setup: expected local PostgreSQL database virtualeculab. Check project .env and inherited DATABASE_URL without sharing credentials."
        )

    # create_all() creates missing tables. Existing tables and data stay
    # in place. Changes to existing columns require a schema migration.
    Base.metadata.create_all(bind=engine)
    print("Learning tables ready. Existing lesson progress is preserved.")
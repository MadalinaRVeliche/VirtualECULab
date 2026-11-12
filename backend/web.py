"""Serve the production React build alongside the FastAPI routes."""

from pathlib import Path

from fastapi.staticfiles import StaticFiles

from backend.main import app

# The Docker build copies the compiled React files to frontend/dist.
# Resolve that directory from this file so startup works from any directory.
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"

# Mount "/" after importing the app. Its API routes are already registered
# and take precedence over the catch-all static mount. HTML mode serves
# index.html at the site root, so the UI and API share the same origin.
app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
"""Serve the production React build alongside the FastAPI routes."""

from pathlib import Path

from fastapi.staticfiles import StaticFiles

from backend.main import app

frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
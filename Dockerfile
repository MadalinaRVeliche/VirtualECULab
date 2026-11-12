# Build the React frontend in a separate stage. The runtime image
# needs the generated static files and does not include Node.js.
FROM node:24-bookworm-slim AS frontend-build
WORKDIR /build

# Install dependencies before copying the source so source-only edits
# can reuse Docker's cached dependency layer.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./

# An empty API base makes browser requests use the current origin.
# backend.web serves both the frontend and the API from that origin.
RUN VITE_API_URL= npm run build

FROM python:3.14-slim-bookworm
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY backend/requirements.txt ./backend/requirements.txt
RUN python -m pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ ./backend/
COPY --from=frontend-build /build/dist ./frontend/dist

# Run the application as an unprivileged user inside the container.
USER 10001:10001
EXPOSE 10000

# Require the database URL from the hosting environment. Create any
# missing tables before serving traffic. exec gives Uvicorn the container's
# main process slot so it receives shutdown signals directly.
CMD ["sh", "-ec", ": \"${DATABASE_URL:?Set DATABASE_URL in the hosting dashboard}\"; python -m backend.init_db; exec python -m uvicorn backend.web:app --host 0.0.0.0 --port \"${PORT:-10000}\""]
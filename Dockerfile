FROM node:24-bookworm-slim AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN VITE_API_URL= npm run build

FROM python:3.14-slim-bookworm
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY backend/requirements.txt ./backend/requirements.txt
RUN python -m pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ ./backend/
COPY --from=frontend-build /build/dist ./frontend/dist
USER 10001:10001
EXPOSE 10000
CMD ["sh", "-ec", ": \"${DATABASE_URL:?Set DATABASE_URL in the hosting dashboard}\"; python -m backend.init_db; exec python -m uvicorn backend.web:app --host 0.0.0.0 --port \"${PORT:-10000}\""]
FROM python:3.12-slim

# Copy uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy pyproject.toml to install dependencies first (caching layer)
COPY pyproject.toml /app/

# Install dependencies using uv to system python
RUN uv pip install --no-cache --system -r pyproject.toml

# Copy the rest of the application
COPY src /app/src
COPY README.md /app/

# Install the package itself
RUN uv pip install --no-cache --system -e .

# Expose port (default 8080)
EXPOSE 8080

# Set database path to writeable tmp directory
ENV SESSIONS_DB_PATH=/tmp/sessions.db

# Run as non-root user
RUN useradd -u 10001 -m appuser
USER appuser

# Start uvicorn
CMD ["sh", "-c", "uvicorn citizenbenefits.web:app --host 0.0.0.0 --port ${PORT:-8080}"]

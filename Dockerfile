FROM python:3.13-slim

# Pin Poetry version for reproducibility
ENV POETRY_VERSION=1.8.2
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies and Poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get purge -y --auto-remove curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Use Poetry's recommended install path and disable venv creation for Docker
RUN poetry config virtualenvs.create false

WORKDIR /app

# Copy only dependency files first for better cache usage
COPY pyproject.toml poetry.lock /app/

# Install dependencies
RUN poetry install --no-interaction --no-root

# Now copy the rest of the application
COPY . /app/

# (Optional) For production, consider running as a non-root user
# RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
# USER appuser
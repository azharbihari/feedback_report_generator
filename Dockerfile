FROM python:3.13-slim

# Install system dependencies and Poetry
RUN apt-get update && apt-get install -y curl \
 && curl -sSL https://install.python-poetry.org | python3 - \
 && apt-get remove -y curl && apt-get autoremove -y

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-root

# Copy project files
COPY . /app/

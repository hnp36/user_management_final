# Base stage with a Debian Bookworm base image and latest glibc
FROM python:3.12-bookworm as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=true \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    QR_CODE_DIR=/myapp/qr_codes

WORKDIR /myapp

# Install system dependencies without pinning libc-bin version
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libc-bin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in a virtual environment
COPY requirements.txt .
RUN python -m venv /.venv \
    && . /.venv/bin/activate \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

# Runtime stage
FROM python:3.12-slim-bookworm as final

# Install libc-bin without pinning version
RUN apt-get update && apt-get install -y libc-bin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from base
COPY --from=base /.venv /.venv

# Set environment variables
ENV PATH="/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    QR_CODE_DIR=/myapp/qr_codes

WORKDIR /myapp

# Create and switch to a non-root user
RUN useradd -m myuser
USER myuser

# Copy application code with correct ownership
COPY --chown=myuser:myuser . .

# Expose FastAPI port
EXPOSE 8000

# Entry point to run the app
ENTRYPOINT ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]

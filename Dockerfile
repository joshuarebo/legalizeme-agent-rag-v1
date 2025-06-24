FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for AI, PDF, image, and text processing
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    software-properties-common \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    libmagic-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-downloaded wheels for large packages (torch, etc.)
COPY wheels/ /wheels/

COPY requirements-docker-clean.txt ./requirements-docker.txt

# Upgrade pip and install build dependencies first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel packaging cmake

# Copy constraints
COPY cpu-constraints.txt ./

# Use fast legacy resolver to avoid depth errors
ENV PIP_USE_DEPRECATED=legacy-resolver

# Install local wheels first, then all requirements with robust pip options
RUN pip install --no-cache-dir --find-links=/wheels --prefer-binary /wheels/*.whl || true \
 && pip install --no-cache-dir --find-links=/wheels --prefer-binary --no-deps -r cpu-constraints.txt || true

# Full install respecting constraints
RUN pip install --no-cache-dir --default-timeout=100 --retries=10 --prefer-binary --find-links=/wheels -r requirements-docker.txt -c cpu-constraints.txt

COPY . .

EXPOSE 8000

# Debug: Print Python and pip versions, and installed packages
RUN python --version && pip --version && pip list

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

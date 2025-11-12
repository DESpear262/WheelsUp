# WheelsUp ETL Pipeline Dockerfile
# Optimized for production with security best practices

FROM python:3.14-alpine

# Install system dependencies for all required packages
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    curl \
    postgresql-dev \
    build-base \
    tiff-dev \
    jpeg-dev \
    openjpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    libwebp-dev \
    tcl-dev \
    tk-dev \
    harfbuzz-dev \
    fribidi-dev \
    libxcb-dev \
    libxext-dev \
    libxrender-dev \
    pixman-dev \
    cairo-dev \
    pango-dev \
    gdk-pixbuf-dev \
    tesseract-ocr \
    tesseract-ocr-data-eng

# Create non-root user first
RUN addgroup -g 1001 -S etluser && \
    adduser -u 1001 -S etluser -G etluser

# Set working directory
WORKDIR /app

# Change ownership of working directory
RUN chown etluser:etluser /app

# Copy requirements first for better caching
COPY --chown=etluser:etluser requirements.txt .

# Install Python dependencies as non-root user
USER etluser
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy source code
COPY --chown=etluser:etluser . .

# Add user bin to PATH
ENV PATH="/home/etluser/.local/bin:$PATH"

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port for potential API endpoints
EXPOSE 8000

# Health check - verify Python can import key modules
HEALTHCHECK --interval=60s --timeout=30s --start-period=30s --retries=3 \
    CMD python -c "import sys; import trafilatura; import scrapy; print('ETL health check passed')" || exit 1

# Default command (can be overridden by docker-compose)
CMD ["python", "--version"]

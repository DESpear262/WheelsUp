# WheelsUp ETL Pipeline Dockerfile
FROM python:3.14-alpine

# Set working directory
WORKDIR /app

# Install system dependencies
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
    gdk-pixbuf-dev

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create non-root user
RUN adduser -D -s /bin/sh -u 1001 etluser && \
    chown -R etluser:etluser /app
USER etluser

# Expose port (if needed for API)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command (can be overridden)
CMD ["python", "--version"]

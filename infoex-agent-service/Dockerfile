# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app app/

# Copy data directory if it exists (for templates/constants)
# Create empty data directory if not
RUN mkdir -p data

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port (Render will override this)
EXPOSE 8000

# Run the application
# Use shell form to allow environment variable expansion
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data and logs directories
RUN mkdir -p /app/data /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:////app/data/dmarc_reports.db

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose Flask port
EXPOSE 5000

# Run entrypoint script
ENTRYPOINT ["/app/docker/entrypoint.sh"]

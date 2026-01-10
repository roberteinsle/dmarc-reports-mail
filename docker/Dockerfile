FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security first
RUN useradd -m -u 1000 appuser

# Copy application code and set ownership
COPY --chown=appuser:appuser . .

# Create data and logs directories with proper ownership
RUN mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app/data /app/logs && \
    chmod 755 /app/data /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:////app/data/dmarc_reports.db

USER appuser

# Expose Flask port
EXPOSE 5000

# Run entrypoint script
ENTRYPOINT ["/app/docker/entrypoint.sh"]

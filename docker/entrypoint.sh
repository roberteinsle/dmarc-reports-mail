#!/bin/bash
set -e

echo "Starting DMARC Reports Mail application..."

# Ensure data directories exist (in case volumes override them)
echo "Creating data directories..."
mkdir -p /app/data /app/logs

# Verify we can write to these directories
if [ ! -w "/app/data" ]; then
    echo "ERROR: Cannot write to /app/data directory!"
    echo "Current user: $(whoami)"
    echo "Directory permissions: $(ls -ld /app/data)"
    exit 1
fi

# Wait a moment for any external services to be ready
sleep 2

# Run database migrations
echo "Running database migrations..."
alembic upgrade head || echo "No migrations to run or alembic not configured yet"

# Initialize database if it doesn't exist
if [ ! -f "/app/data/dmarc_reports.db" ]; then
    echo "Database file not found, initializing..."
    python -c "from app import create_app; from app.models.database import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized')" || echo "Failed to initialize database"
fi

# Start the application
echo "Starting Flask application..."
exec python run.py

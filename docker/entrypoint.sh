#!/bin/bash
set -e

echo "Starting DMARC Reports Mail application..."

# Wait a moment for any external services to be ready
sleep 2

# Run database migrations
echo "Running database migrations..."
alembic upgrade head || echo "No migrations to run or alembic not configured yet"

# Start the application
echo "Starting Flask application..."
exec python run.py

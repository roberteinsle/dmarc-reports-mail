#!/bin/bash
set -e

echo "Starting DMARC Reports Mail application..."
echo "Running as: $(whoami) (UID=$(id -u), GID=$(id -g))"

# Ensure data directories exist
echo "Creating data directories..."
mkdir -p /app/data /app/logs

# Fix permissions for Docker volumes (running as root initially)
echo "Fixing volume permissions..."
chown -R appuser:appuser /app/data /app/logs
chmod -R 755 /app/data /app/logs

# Display directory information for debugging
echo "Directory information:"
ls -ld /app/data /app/logs

# Test write permissions as appuser
echo "Testing write permissions as appuser..."
gosu appuser touch /app/data/.write_test || {
    echo "ERROR: appuser cannot write to /app/data even after permission fix!"
    echo "Volume details:"
    ls -la /app/data/
    exit 1
}
gosu appuser rm -f /app/data/.write_test
echo "Write permissions verified successfully."

# Wait a moment for any external services to be ready
sleep 2

# Run database migrations as appuser
echo "Running database migrations as appuser..."
gosu appuser alembic upgrade head || echo "No migrations to run or alembic not configured yet"

# Initialize database if it doesn't exist
if [ ! -f "/app/data/dmarc_reports.db" ]; then
    echo "Database file not found, initializing as appuser..."
    gosu appuser python -c "from app import create_app; from app.models.database import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized')" || {
        echo "ERROR: Failed to initialize database"
        echo "Checking database directory permissions:"
        ls -la /app/data/
        exit 1
    }

    # Verify database was created
    if [ -f "/app/data/dmarc_reports.db" ]; then
        echo "Database created successfully:"
        ls -lh /app/data/dmarc_reports.db*
    else
        echo "ERROR: Database file was not created!"
        exit 1
    fi
else
    echo "Database file exists:"
    ls -lh /app/data/dmarc_reports.db*
fi

# Test database connectivity as appuser
echo "Testing database connectivity..."
gosu appuser python -c "
from app import create_app
from app.models.database import db
from sqlalchemy import text
app = create_app()
with app.app_context():
    try:
        with db.engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('Database connection test: SUCCESS')
    except Exception as e:
        print(f'Database connection test: FAILED - {e}')
        import traceback
        traceback.print_exc()
        exit(1)
" || exit 1

# Start the application as appuser
echo "Starting Flask application as appuser..."
exec gosu appuser python run.py

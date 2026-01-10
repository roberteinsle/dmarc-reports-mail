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
chmod -R 775 /app/data /app/logs

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

# Additional diagnostics for database directory
echo "Additional filesystem diagnostics:"
echo "  Mount point: $(df -h /app/data | tail -1)"
echo "  Directory ownership: $(stat -c '%U:%G' /app/data)"
echo "  Directory permissions: $(stat -c '%a' /app/data)"
echo "  Current user running test: $(gosu appuser whoami)"
echo "  Can create file: $(gosu appuser sh -c 'touch /app/data/.test && echo YES && rm /app/data/.test || echo NO')"

# Wait a moment for any external services to be ready
sleep 2

# Run database migrations as appuser
echo "Running database migrations as appuser..."
gosu appuser alembic upgrade head || echo "No migrations to run or alembic not configured yet"

# Check if database exists and has tables
echo "Checking database status..."
if [ ! -f "/app/data/dmarc_reports.db" ]; then
    echo "Database file not found, creating new database..."

    # First, test if SQLite can work at all in this directory
    echo "Testing SQLite directly..."
    gosu appuser python3 -c "
import sqlite3
import os
db_path = '/app/data/test.db'
try:
    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE test (id INTEGER)')
    conn.close()
    os.remove(db_path)
    print('  SQLite direct test: SUCCESS')
except Exception as e:
    print(f'  SQLite direct test: FAILED - {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"
else
    echo "Database file exists:"
    ls -lh /app/data/dmarc_reports.db*
fi

# Always ensure tables exist (idempotent operation)
echo "Ensuring database tables exist..."
gosu appuser python -c "
from app import create_app
from app.models.database import db
app = create_app()
with app.app_context():
    try:
        db.create_all()
        print('Database tables created/verified successfully')
    except Exception as e:
        print(f'ERROR: Failed to create database tables - {e}')
        import traceback
        traceback.print_exc()
        exit(1)
" || {
    echo "ERROR: Failed to initialize database tables"
    echo "Checking database directory permissions:"
    ls -la /app/data/
    echo "Checking DATABASE_URL:"
    gosu appuser python -c "import os; print(f'DATABASE_URL={os.getenv(\"DATABASE_URL\")}')"
    exit 1
}

echo "Database initialization complete:"
ls -lh /app/data/dmarc_reports.db* 2>/dev/null || echo "No database files found"

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

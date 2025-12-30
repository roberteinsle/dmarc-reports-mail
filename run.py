"""
Application entry point for DMARC Reports Mail.
"""
import signal
import sys
from app import create_app
from app.services.scheduler_service import init_scheduler, stop_scheduler

# Create Flask app
app = create_app()


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    app.logger.info("Received shutdown signal, stopping scheduler...")
    stop_scheduler()
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


if __name__ == '__main__':
    # Initialize and start the scheduler
    app.logger.info("Starting DMARC Reports Mail application...")
    init_scheduler(app)
    app.logger.info("Scheduler initialized successfully")

    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config.get('DEBUG', False),
        use_reloader=False  # Disable reloader to prevent scheduler duplication
    )

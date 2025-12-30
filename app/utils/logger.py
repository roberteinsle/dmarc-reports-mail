"""
Logging configuration for the DMARC Reports Mail application.
"""
import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(app):
    """
    Configure application logging with rotating file handlers.

    Args:
        app: Flask application instance
    """
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Remove default handlers
    app.logger.handlers.clear()

    # Set log level from config
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    app.logger.setLevel(log_level)

    # Application log handler
    app_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))

    # Error log handler
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s\n'
        'Exception:\n%(exc_info)s\n'
    ))

    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if app.config.get('DEBUG') else logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))

    # Add handlers to app logger
    app.logger.addHandler(app_handler)
    app.logger.addHandler(error_handler)
    app.logger.addHandler(console_handler)

    app.logger.info('Logging configured successfully')

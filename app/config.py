"""
Configuration management for DMARC Reports Mail application.
"""
import os
import secrets
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
    DEBUG = False
    TESTING = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///dmarc_reports.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # IMAP Configuration
    IMAP_HOST = os.getenv('IMAP_HOST')
    IMAP_PORT = int(os.getenv('IMAP_PORT', 993))
    IMAP_USER = os.getenv('IMAP_USER')
    IMAP_PASSWORD = os.getenv('IMAP_PASSWORD')
    IMAP_FOLDER = os.getenv('IMAP_FOLDER', 'INBOX')

    # Claude API Configuration
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

    # SMTP Configuration
    SMTP_HOST = os.getenv('SMTP_HOST')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SMTP_FROM = os.getenv('SMTP_FROM')
    ALERT_RECIPIENT = os.getenv('ALERT_RECIPIENT')

    # Scheduler Configuration
    SCHEDULER_INTERVAL_MINUTES = int(os.getenv('SCHEDULER_INTERVAL_MINUTES', 5))

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @staticmethod
    def validate():
        """Validate that all required configuration variables are set."""
        required_vars = {
            'IMAP_HOST': Config.IMAP_HOST,
            'IMAP_USER': Config.IMAP_USER,
            'IMAP_PASSWORD': Config.IMAP_PASSWORD,
            'ANTHROPIC_API_KEY': Config.ANTHROPIC_API_KEY,
            'SMTP_HOST': Config.SMTP_HOST,
            'SMTP_USER': Config.SMTP_USER,
            'SMTP_PASSWORD': Config.SMTP_PASSWORD,
            'ALERT_RECIPIENT': Config.ALERT_RECIPIENT,
        }

        missing = [var for var, value in required_vars.items() if not value]

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Please check your .env file or environment variables."
            )


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///dmarc_reports_dev.db')
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # Use environment variable or default Docker volume path
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:////app/data/dmarc_reports.db')


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SCHEDULER_INTERVAL_MINUTES = 1  # Shorter interval for testing

    # Override validation for testing (use mock credentials)
    @staticmethod
    def validate():
        pass


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    Get configuration object based on environment.

    Args:
        config_name: Configuration name ('development', 'production', 'testing')
                     If None, uses FLASK_ENV environment variable

    Returns:
        Configuration class
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    return config.get(config_name, config['default'])

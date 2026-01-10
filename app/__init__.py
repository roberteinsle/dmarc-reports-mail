"""
Flask application factory for DMARC Reports Mail.
"""
from flask import Flask
from app.config import get_config
from app.models.database import db
from app.utils.logger import setup_logging


def create_app(config_name=None):
    """
    Create and configure the Flask application.

    Args:
        config_name: Configuration name ('development', 'production', 'testing')

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Validate configuration
    try:
        config_class.validate()
    except ValueError as e:
        app.logger.error(f"Configuration validation failed: {e}")
        # In production, we want to fail fast if config is invalid
        if not app.config.get('TESTING'):
            raise

    # Initialize extensions
    db.init_app(app)

    # Setup logging
    setup_logging(app)

    # Database tables are created by entrypoint.sh before app starts
    # This ensures /app/data directory exists with proper permissions first

    # Register blueprints
    from app.routes import dashboard
    app.register_blueprint(dashboard.bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Internal server error: {error}', exc_info=True)
        return {'error': 'Internal server error'}, 500

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    app.logger.info(f'Flask app created with config: {config_name or "default"}')

    return app

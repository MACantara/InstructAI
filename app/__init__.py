from flask import Flask, render_template
from flask_debugtoolbar import DebugToolbarExtension
import logging
from logging.handlers import RotatingFileHandler
import os
from config import config

toolbar = DebugToolbarExtension()

def configure_logging(app):
    """Configure logging for the application"""
    # Set up basic logging configuration
    logging.basicConfig(level=logging.DEBUG if app.debug else logging.INFO)
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Create file handler
    file_handler = RotatingFileHandler('logs/instructai.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: [%(name)s] %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: [%(name)s] %(message)s'
    ))
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configure app logger
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)
    return app

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    toolbar.init_app(app)
    
    # Configure logging
    configure_logging(app)
    
    # Register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f'Page not found: {error}')
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}')
        return render_template('errors/500.html'), 500
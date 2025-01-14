from flask import Flask, render_template
import logging
from logging.handlers import RotatingFileHandler
import os
from config import config

def configure_logging(app):
    """Configure logging for the application"""
    # Remove all existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'instructai.log')
    
    try:
        # Create file handler with proper permissions
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=1024 * 1024,  # 1MB
            backupCount=5,
            delay=True,  # Delay file creation until first log
            mode='a',  # Append mode
            encoding='utf-8'
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: [%(name)s] %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not create log file: {e}")
        file_handler = None
    
    # Create console handler (always works)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(levelname)s: [%(name)s] %(message)s')
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.DEBUG)
    
    # Configure root logger
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    if file_handler:
        root_logger.addHandler(file_handler)
    
    # Configure app and module loggers
    loggers = [
        app.logger,
        logging.getLogger('app'),
        logging.getLogger('werkzeug'),
        logging.getLogger('app.utils.ai_helper')
    ]
    
    for logger in loggers:
        logger.propagate = False
        logger.handlers = []
        logger.addHandler(console_handler)
        if file_handler:
            logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)
    
    if not file_handler:
        app.logger.warning("File logging disabled due to permission issues")
    
    return app

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
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
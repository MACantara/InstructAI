from flask import Flask, render_template
import logging
from logging.handlers import RotatingFileHandler
import os
from config import config
import sys

def configure_logging(app):
    if app.config['ENV'] == 'production':
        # In production (Vercel), log to stdout
        handler = logging.StreamHandler(sys.stdout)
    else:
        # In development, log to file
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'instructai.log')
        handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=10)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

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
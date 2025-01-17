import os
from flask import Flask, render_template
from dotenv import load_dotenv
import logging
from logging.config import dictConfig
from config import config

# Configure logging with just stream handler
dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

def create_app(config_name='default'):
    """Application factory function"""
    # Load environment variables
    load_dotenv()
    
    app = Flask(__name__)
    
    # Load config
    app.config.from_object(config[config_name])
    
    # Register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
        
    return app
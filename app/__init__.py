from flask import Flask, render_template
from config import config

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
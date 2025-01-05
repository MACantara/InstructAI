from flask import Flask

def create_app(config_class=None):
    app = Flask(__name__)
    
    # Apply configuration if provided
    if config_class:
        config_class.init_app(app)
    
    # Import and register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
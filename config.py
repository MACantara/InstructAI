from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Config:
    # Base configuration settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Additional configuration options
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    DEBUG_TB_TEMPLATE_EDITOR_ENABLED = True
    FLASK_DEBUG = True

    @classmethod
    def init_app(cls, app):
        """
        Initialize application with configuration settings.
        Allows for flexible configuration extension.
        """
        # Set core configurations
        app.config['SECRET_KEY'] = cls.SECRET_KEY
        app.config['DEBUG'] = cls.DEBUG

        # Optional configurations (only set if not None)
        optional_configs = [
            'SQLALCHEMY_DATABASE_URI', 
            'SQLALCHEMY_TRACK_MODIFICATIONS',
            'MAIL_SERVER', 
            'MAIL_PORT', 
            'MAIL_USE_TLS',
            'MAIL_USERNAME', 
            'MAIL_PASSWORD',
            'GEMINI_API_KEY'
        ]

        for config in optional_configs:
            value = getattr(cls, config, None)
            if value is not None:
                app.config[config] = value

        return app

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///dev_database.db')
    FLASK_ENV = 'development'
    EXPLAIN_TEMPLATE_LOADING = True
    TEMPLATES_AUTO_RELOAD = True

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost/proddb')

class TestingConfig(Config):
    TESTING = True
    # Testing-specific configurations
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Mapping of config names to classes
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
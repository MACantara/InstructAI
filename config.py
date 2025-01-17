import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base config."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-please-change')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    POSTGRES_URL = os.getenv('POSTGRES_URL')
    POSTGRES_URL_NON_POOLING = os.getenv('POSTGRES_URL_NON_POOLING')
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    LOG_PATH = os.getenv('LOG_PATH', os.path.join(os.getcwd(), 'logs'))

class DevelopmentConfig(Config):
    FLASK_ENV = 'development'
    DEBUG = True
    TESTING = False
    LOG_PATH = os.path.join(os.getcwd(), 'logs', 'development')

class TestingConfig(Config):
    FLASK_ENV = 'testing'
    DEBUG = True
    TESTING = True
    LOG_PATH = os.path.join(os.getcwd(), 'logs', 'testing')

class ProductionConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    LOG_PATH = '/tmp/logs'  # Use /tmp for production environments

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
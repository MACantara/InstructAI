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

class DevelopmentConfig(Config):
    FLASK_ENV = 'development'
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    FLASK_ENV = 'testing'
    DEBUG = True
    TESTING = True

class ProductionConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
from app import create_app
from config import config

if __name__ == '__main__':
    config_name = 'development'
    app = create_app(config_name)
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
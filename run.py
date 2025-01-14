from app import create_app
from config import config

# Create the app instance for Vercel
app = create_app('production')

if __name__ == '__main__':
    # This block will only run for local development
    config_name = 'development'
    app = create_app(config_name)
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
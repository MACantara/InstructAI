# Flask Web Template

## Overview

This is a modular and extensible Flask web application template designed to provide a robust starting point for web development projects. The template incorporates best practices for project structure, configuration management, and frontend design.

## Features

- 🚀 Modular Flask Application Structure
- 🔧 Flexible Configuration Management
- 💅 Modern CSS with Root Variables
- 📱 Responsive Design
- 🛡️ Environment-based Configuration
- 🧩 Easy to Extend and Customize

## Project Structure

```bash
flask_web_template/
│
├── app/
│   ├── __init__.py         # App factory and initialization
│   ├── routes.py           # Application routes
│   │
│   ├── static/             # Static assets
│   │   ├── css/            # Stylesheets
│   │   │   ├── base.css
│   │   │   └── index.css
│   │   │
│   │   └── js/             # JavaScript files
│   │       ├── base.js
│   │       └── index.js
│   │
│   └── templates/          # HTML templates
│       ├── base.html
│       └── index.html
├── .gitignore              # Ignore files
├── LICENSE                 # License information
├── config.py               # Configuration management
├── run.py                  # Application entry point
└── requirements.txt        # Project dependencies
```

# Project dependencies


## Prerequisites

- Python 3.8+
- pip
- virtualenv (recommended)

## Setup and Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/flask_web_template.git
   cd flask_web_template
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

# Configuration

The template supports multiple configuration environments:

- `DevelopmentConfig`: Default configuration for local development.
- `ProductionConfig`: Configuration for production deployment.
- `TestingConfig`: Configuration for testing.

# Switching Configurations

Set the `FLASK_CONFIG` environment variable to switch configurations:

## For development (default)

```bash
export FLASK_CONFIG=development
```

## For production

```bash
export FLASK_CONFIG=production
```

## For testing

```bash
export FLASK_CONFIG=testing
```

# Running the Application

```bash
# Development mode
python run.py
```

```bash
# Or use the Flask CLI
flask run
```

## Using Environment Variables

```bash
# Production mode
FLASK_CONFIG=production python run.py
```

```bash
# Testing mode
FLASK_CONFIG=testing python run.py
```

# Customization

Customize the look and feel by modifying root variables in `app/static/css/base.css`:

```css
:root {
    /* Color Palette */
    --primary-color: #3498db;
    --secondary-color: #2ecc71;
    --background-color: #f4f4f4;
    --text-color-dark: #333;
    --text-color-light: #666;
    
    /* Typography */
    --font-family-primary: Arial, sans-serif;
    --font-size-base: 16px;
    --font-size-heading: 1.5rem;
    
    /* Spacing */
    --spacing-small: 10px;
    --spacing-medium: 20px;
    --spacing-large: 30px;
    
    /* Shadows and Effects */
    --box-shadow-default: 0 2px 4px rgba(0, 0, 0, 0.1);
}
```

# Adding New Routes

Edit `app/routes.py` to add new routes and views.

# Configuration Extensions

Modify `config.py` to add or extend configuration options.

# Best practices

- Keep configuration in `config.py`.
- Use environment variables for sensitive information.
- Separate concerns between routes, templates, and static files.
- Utilize CSS root variables for consistent theming.

# Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

# License

Distributed under the MIT License. See `LICENSE` for more information.

# Contact

You can find me on [GitHub](https://github.com/MACantara) for any questions or feedback.
from flask import Flask
from infra.api import api_blueprint
import logging
import os


def create_app():
    """Initialize and configure the Flask application"""
    app = Flask(__name__)

    # Configuration
    app.config['AWS_REGION'] = os.environ.get('AWS_REGION', 'eu-central-1')
    app.config['DYNAMODB_TABLE'] = os.environ.get('DYNAMODB_TABLE', 'tv_show_tracker')

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Register blueprints
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
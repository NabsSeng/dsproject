"""
Main Flask application for the code generation and deployment API.
"""

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from src.routes.code_generator import code_generator_bp
from src.middleware.validation import ValidationError
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['DEBUG'] = os.getenv('FLASK_ENV') == 'development'
    
    # Setup CORS
    CORS(app, origins="*")
    
    # Setup logging
    setup_logger()
    
    # Register blueprints
    app.register_blueprint(code_generator_bp, url_prefix='/api')
    
    # Error handlers
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return jsonify({'error': str(e)}), 400
    
    @app.errorhandler(Exception)
    def handle_generic_error(e):
        logging.error(f"Unhandled exception: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'service': 'code-generator-api'})
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
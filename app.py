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
from src.services.cache_service import cache_service

# Load environment variables
load_dotenv()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['DEBUG'] = os.getenv('FLASK_ENV') == 'development'
    
    # Setup CORS - Allow all origins and methods for web app integration
    CORS(app, 
         origins="*",
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization"])
    
    # Setup logging
    setup_logger()
    
    # Make cache service available to the app
    app.cache_service = cache_service
    
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
    
    # Cache management endpoints
    @app.route('/api/cache/info')
    def cache_info():
        """Get cache statistics."""
        info = cache_service.get_cache_info()
        return jsonify(info)
    
    @app.route('/api/cache/clear-expired', methods=['POST'])
    def clear_expired_cache():
        """Clear expired cache entries."""
        cleared_count = cache_service.clear_expired()
        return jsonify({
            'message': f'Cleared {cleared_count} expired cache entries',
            'cleared_count': cleared_count
        })
    
    @app.route('/api/cache/<task_id>', methods=['DELETE'])
    def delete_cache(task_id):
        """Delete cache for specific task ID."""
        success = cache_service.delete(task_id)
        if success:
            return jsonify({'message': f'Cache deleted for task: {task_id}'})
        else:
            return jsonify({'message': f'No cache found for task: {task_id}'}), 404
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
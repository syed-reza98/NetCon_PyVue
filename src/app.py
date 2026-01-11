"""
Improved Flask Application with Best Practices
Author: NetCon Development Team
Date: June 15, 2025
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import HTTPException
from controllers.ej_controller import ej_controller
from controllers.auth_controller import auth_controller
from models import db

def create_app(config_name='development'):
    """Application factory pattern for better testing and configuration"""
    app = Flask(__name__)
      # Configuration Management
    app.config.update({
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-secret-change-in-production'),
        'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL', 'sqlite:///app.db'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'pool_timeout': 20,
            'pool_recycle': -1,
            'pool_pre_ping': True
        },
        # JWT Configuration
        'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-in-production'),
        'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=24),
        'JWT_REFRESH_TOKEN_EXPIRES': timedelta(days=30),
        'JWT_TOKEN_LOCATION': ['headers'],
        'JWT_HEADER_NAME': 'Authorization',
        'JWT_HEADER_TYPE': 'Bearer',
        # Security Headers
        'WTF_CSRF_ENABLED': True,
        'SESSION_COOKIE_SECURE': True,
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        # API Settings
        'MAX_CONTENT_LENGTH': 100 * 1024 * 1024,  # 100MB max file size
        'UPLOAD_FOLDER': 'uploads',
        'ALLOWED_EXTENSIONS': {'txt', 'log'},
    })
      # Initialize extensions
    db.init_app(app)
    
    # Initialize JWT Manager
    jwt = JWTManager(app)
    
    # CORS Configuration - More restrictive for production
    cors_origins = os.environ.get('CORS_ORIGINS', '*').split(',')
    CORS(app, origins=cors_origins, supports_credentials=True)
      # Rate Limiting
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
    limiter.init_app(app)
    
    # Configure Logging
    configure_logging(app)
    
    # Register Blueprints
    app.register_blueprint(ej_controller, url_prefix='/api/ej')
    app.register_blueprint(auth_controller, url_prefix='/api')
    
    # Error Handlers
    register_error_handlers(app)
    
    # Request/Response Middleware
    register_middleware(app)
      # Health Check Endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '1.0.0'
        })
    
    # Create tables
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Failed to create database tables: {e}")
    
    return app

def configure_logging(app):
    """Configure application logging"""
    if not app.debug:
        # Production logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s',
            handlers=[
                logging.FileHandler('logs/netcon_backend.log'),
                logging.StreamHandler()
            ]
        )
    else:
        # Development logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(message)s'
        )

def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        app.logger.warning(f"Bad Request: {request.url} - {error}")
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        app.logger.warning(f"Unauthorized access attempt: {request.url}")
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        app.logger.warning(f"Forbidden access: {request.url}")
        return jsonify({
            'error': 'Forbidden',
            'message': 'Insufficient permissions'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        app.logger.warning(f"File too large: {request.url}")
        return jsonify({
            'error': 'File Too Large',
            'message': 'The uploaded file exceeds the maximum size limit'
        }), 413
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        app.logger.warning(f"Rate limit exceeded: {request.remote_addr}")
        return jsonify({
            'error': 'Too Many Requests',
            'message': 'Rate limit exceeded. Please try again later.'
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal Server Error: {error}")
        db.session.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_exception(e):
        """Handle HTTP exceptions with JSON responses"""
        app.logger.error(f"HTTP Exception: {e}")
        return jsonify({
            'error': e.name,
            'message': e.description
        }), e.code

def register_middleware(app):
    """Register request/response middleware"""
    
    @app.before_request
    def before_request():
        """Log incoming requests and validate headers"""
        app.logger.info(f"{request.method} {request.url} - {request.remote_addr}")
        
        # Validate Content-Type for POST requests
        if request.method == 'POST' and request.content_type:
            if not (request.content_type.startswith('application/json') or 
                   request.content_type.startswith('multipart/form-data')):
                return jsonify({
                    'error': 'Unsupported Media Type',
                    'message': 'Content-Type must be application/json or multipart/form-data'
                }), 415
    
    @app.after_request
    def after_request(response):
        """Add security headers to all responses"""
        # Security Headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Log response
        app.logger.info(f"Response: {response.status_code} - {request.url}")
        return response

# Application factory instantiation
app = create_app()

if __name__ == '__main__':
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Development server configuration
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    app.run(
        debug=debug_mode,
        host=host,
        port=port,
        threaded=True
    )

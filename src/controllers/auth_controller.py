"""
Enhanced Authentication Controller with Security Best Practices
Author: NetCon Development Team
Date: June 15, 2025
"""

import logging
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
import re
from models import db, User

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
auth_controller = Blueprint('auth_controller', __name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

def validate_input(data, required_fields):
    """Validate and sanitize input data"""
    errors = []
    
    # Check required fields
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"{field} is required")
        elif isinstance(data[field], str):
            # Sanitize string inputs
            data[field] = data[field].strip()
            if not data[field]:
                errors.append(f"{field} cannot be empty")
    
    return errors

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return "Invalid email format"
    if len(email) > 255:
        return "Email too long"
    return None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    if len(password) > 128:
        return "Password too long"
    if not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return "Password must contain at least one digit"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return "Password must contain at least one special character"
    return None

def validate_username(username):
    """Validate username"""
    if len(username) < 3:
        return "Username must be at least 3 characters long"
    if len(username) > 50:
        return "Username too long"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return "Username can only contain letters, numbers, and underscores"
    return None

def generate_token(user_id, username):
    """Generate JWT token using Flask-JWT-Extended"""
    additional_claims = {
        'username': username,
        'user_id': user_id
    }
    access_token = create_access_token(
        identity=str(user_id),  # Convert to string as required by Flask-JWT-Extended
        additional_claims=additional_claims
    )
    return access_token

def verify_token(token):
    """Verify JWT token - This function is now replaced by @jwt_required decorator"""
    # This function is kept for backwards compatibility but should use @jwt_required decorator
    # The verification is now handled by Flask-JWT-Extended automatically
    return None

def require_auth(f):
    """Decorator to require authentication using Flask-JWT-Extended"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        # Get current user ID from JWT (convert back to int)
        current_user_id = int(get_jwt_identity())
        
        # Get user from database
        user = User.query.get(current_user_id)
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

@auth_controller.route('/register', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limit registration attempts
def register():
    """User registration with comprehensive validation"""
    try:
        # Get and validate JSON data
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['email', 'username', 'password', 'repassword']
        validation_errors = validate_input(data, required_fields)
        
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        email = data['email'].lower()  # Normalize email
        username = data['username']
        password = data['password']
        repassword = data['repassword']
        
        # Additional validation
        email_error = validate_email(email)
        if email_error:
            return jsonify({'error': email_error}), 400
        
        username_error = validate_username(username)
        if username_error:
            return jsonify({'error': username_error}), 400
        
        password_error = validate_password(password)
        if password_error:
            return jsonify({'error': password_error}), 400
        
        if password != repassword:
            return jsonify({'error': 'Passwords do not match'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            if existing_user.email == email:
                return jsonify({'error': 'Email already registered'}), 409
            else:
                return jsonify({'error': 'Username already taken'}), 409
        
        # Create new user
        new_user = User(
            email=email,
            username=username
        )
        new_user.password = password  # This will hash the password
        
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"New user registered: {username} ({email})")
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': new_user.id,
                'email': new_user.email,
                'username': new_user.username
            }
        }), 201
    
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Database integrity error during registration: {e}")
        return jsonify({
            'error': 'Registration failed',
            'message': 'User with this email or username already exists'
        }), 409
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error during registration: {e}")
        return jsonify({
            'error': 'Registration failed',
            'message': 'An unexpected error occurred'
        }), 500

@auth_controller.route('/login', methods=['POST'])
@limiter.limit("10 per minute")  # Rate limit login attempts
def login():
    """User login with security features"""
    try:
        # Get and validate JSON data
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['email', 'password']
        validation_errors = validate_input(data, required_fields)
        
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        email = data['email'].lower()  # Normalize email
        password = data['password']
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            logger.warning(f"Login attempt with non-existent email: {email}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if account is locked
        if user.is_locked:
            logger.warning(f"Login attempt on locked account: {email}")
            return jsonify({
                'error': 'Account locked',
                'message': 'Account temporarily locked due to multiple failed login attempts'
            }), 423
        
        # Check if account is active
        if not user.is_active:
            logger.warning(f"Login attempt on inactive account: {email}")
            return jsonify({'error': 'Account inactive'}), 403
        
        # Verify password
        if not user.verify_password(password):
            user.increment_failed_login()
            db.session.commit()
            
            logger.warning(f"Failed login attempt for: {email}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Successful login
        user.reset_failed_login()
        db.session.commit()
        
        # Generate token
        token = generate_token(user.id, user.username)
        
        logger.info(f"Successful login: {user.username} ({email})")
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'role': user.role,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        return jsonify({
            'error': 'Login failed',
            'message': 'An unexpected error occurred'
        }), 500

@auth_controller.route('/logout', methods=['POST'])
@require_auth
def logout():
    """User logout"""
    logger.info(f"User logout: {request.current_user.username}")
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_controller.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get user profile"""
    user = request.current_user
    return jsonify({
        'user': user.to_dict()
    }), 200

@auth_controller.route('/profile', methods=['PUT'])
@require_auth
@limiter.limit("5 per minute")
def update_profile():
    """Update user profile"""
    try:
        user = request.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Allow updating only specific fields
        allowed_fields = ['username']
        updates = {}
        
        for field in allowed_fields:
            if field in data:
                if field == 'username':
                    username_error = validate_username(data[field])
                    if username_error:
                        return jsonify({'error': username_error}), 400
                    
                    # Check if username is already taken
                    existing = User.query.filter(
                        User.username == data[field],
                        User.id != user.id
                    ).first()
                    if existing:
                        return jsonify({'error': 'Username already taken'}), 409
                
                updates[field] = data[field]
        
        # Apply updates
        for field, value in updates.items():
            setattr(user, field, value)
        
        db.session.commit()
        
        logger.info(f"Profile updated for user: {user.username}")
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating profile: {e}")
        return jsonify({
            'error': 'Update failed',
            'message': 'An unexpected error occurred'
        }), 500

@auth_controller.route('/change-password', methods=['POST'])
@require_auth
@limiter.limit("3 per minute")
def change_password():
    """Change user password"""
    try:
        user = request.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['current_password', 'new_password', 'confirm_password']
        validation_errors = validate_input(data, required_fields)
        
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        confirm_password = data['confirm_password']
        
        # Verify current password
        if not user.verify_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Validate new password
        password_error = validate_password(new_password)
        if password_error:
            return jsonify({'error': password_error}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'New passwords do not match'}), 400
        
        if current_password == new_password:
            return jsonify({'error': 'New password must be different from current password'}), 400
        
        # Update password
        user.password = new_password
        db.session.commit()
        
        logger.info(f"Password changed for user: {user.username}")
        
        return jsonify({'message': 'Password changed successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error changing password: {e}")
        return jsonify({
            'error': 'Password change failed',
            'message': 'An unexpected error occurred'
        }), 500

@auth_controller.route('/verify-token', methods=['POST'])
@jwt_required()
def verify_user_token():
    """Verify if token is valid using Flask-JWT-Extended"""
    try:
        # Get current user ID from JWT
        current_user_id = get_jwt_identity()
        
        # Get user from database
        user = User.query.get(current_user_id)
        if not user or not user.is_active:
            return jsonify({'valid': False, 'error': 'User not found or inactive'}), 401
        
        return jsonify({
            'valid': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return jsonify({'valid': False, 'error': 'Token verification failed'}), 500

@auth_controller.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded"""
    logger.warning(f"Rate limit exceeded for IP: {request.remote_addr}")
    return jsonify({
        'error': 'Too Many Requests',
        'message': 'Rate limit exceeded. Please try again later.'
    }), 429

# Admin-only routes
@auth_controller.route('/admin/users', methods=['GET'])
@require_auth
def list_users():
    """List all users (Admin only)"""
    if request.current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    users = User.query.all()
    return jsonify({
        'users': [user.to_dict() for user in users]
    }), 200

@auth_controller.route('/admin/users/<int:user_id>/deactivate', methods=['POST'])
@require_auth
def deactivate_user(user_id):
    """Deactivate a user (Admin only)"""
    if request.current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    
    logger.info(f"User deactivated by admin: {user.username}")
    
    return jsonify({'message': 'User deactivated successfully'}), 200

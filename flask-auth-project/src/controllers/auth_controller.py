from flask import Blueprint, request, jsonify
from services.auth_service import AuthService
from flask_jwt_extended import jwt_required, get_jwt_identity

auth_controller = Blueprint('auth_controller', __name__)
auth_service = AuthService()

@auth_controller.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
    
    # Register user
    result = auth_service.register_user(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        role_name=data.get('role', 'user')  # Default to 'user' if not specified
    )
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@auth_controller.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Validate required fields
    if not data.get('username_or_email') or not data.get('password'):
        return jsonify({
            'success': False,
            'message': 'Username/email and password are required'
        }), 400
    
    # Login user
    result = auth_service.login_user(
        username_or_email=data['username_or_email'],
        password=data['password']
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 401

@auth_controller.route('/user', methods=['GET'])
@jwt_required()
def get_user_info():
    user_id = get_jwt_identity()
    user = auth_service.get_user_by_id(user_id)
    
    if user:
        return jsonify({'success': True, 'user': user}), 200
    else:
        return jsonify({'success': False, 'message': 'User not found'}), 404
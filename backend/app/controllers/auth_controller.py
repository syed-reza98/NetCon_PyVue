# controllers/auth_controller.py
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth_controller = Blueprint('auth_controller', __name__)

@auth_controller.route('/register', methods=['OPTIONS'])
def register_options():
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST')
    return response, 200

@auth_controller.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    repassword = data.get('repassword')

    if not email or not username or not password or not repassword:
        return jsonify({'message': 'All fields are required'}), 400
    if password != repassword:
        return jsonify({'message': 'Passwords do not match'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'User already exists'}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(email=email, username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    response = jsonify({'message': 'Registered successfully'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 200

@auth_controller.route('/login', methods=['OPTIONS'])
def login_options():
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST')
    return response, 200

@auth_controller.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid credentials'}), 401

    response = jsonify({
        'token': 'demo-token',
        'user': {'email': user.email, 'username': user.username}
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 200

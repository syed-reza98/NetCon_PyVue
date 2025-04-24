# controllers/auth_controller.py
from flask import Blueprint, request, jsonify
import json
import os

auth_controller = Blueprint('auth_controller', __name__)

USER_FILE = 'users.json'

# Load users from file


def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, 'r') as f:
        return json.load(f)

# Save users to file


def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f)

# Add OPTIONS route handler for CORS preflight requests


@auth_controller.route('/register', methods=['OPTIONS'])
def register_options():
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
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

    users = load_users()
    if email in users:
        return jsonify({'message': 'User already exists'}), 400

    users[email] = {'username': username, 'password': password}
    save_users(users)

    response = jsonify({'message': 'Registered successfully'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 200

# Add OPTIONS route handler for CORS preflight requests


@auth_controller.route('/login', methods=['OPTIONS'])
def login_options():
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST')
    return response, 200


@auth_controller.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    users = load_users()
    user = users.get(email)

    if not user or user['password'] != password:
        return jsonify({'message': 'Invalid credentials'}), 401

    response = jsonify({
        'token': 'demo-token',
        'user': {'email': email, 'username': user['username']}
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 200

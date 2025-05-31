from flask import jsonify, request
from models.user import User
from models.role import Role
from models.permission import Permission
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import logging

# Configure logging for tracking progress and debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EJService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @jwt_required()
    def get_user_info(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first()
        if user:
            return jsonify(user.serialize()), 200
        return jsonify({"msg": "User not found"}), 404

    @jwt_required()
    def update_user_role(self, user_id, role_name):
        user = User.query.filter_by(id=user_id).first()
        role = Role.query.filter_by(name=role_name).first()
        if user and role:
            user.role = role
            user.save()
            return jsonify({"msg": "User role updated successfully"}), 200
        return jsonify({"msg": "User or role not found"}), 404

    def register_user(self, username, password):
        if User.query.filter_by(username=username).first():
            return jsonify({"msg": "User already exists"}), 400
        new_user = User(username=username)
        new_user.set_password(password)
        new_user.save()
        return jsonify({"msg": "User registered successfully"}), 201

    def login_user(self, username, password):
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            access_token = create_access_token(identity=user.id)
            return jsonify(access_token=access_token), 200
        return jsonify({"msg": "Bad username or password"}), 401

    @jwt_required()
    def get_permissions(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first()
        if user:
            permissions = [perm.name for perm in user.role.permissions]
            return jsonify(permissions=permissions), 200
        return jsonify({"msg": "User not found"}), 404
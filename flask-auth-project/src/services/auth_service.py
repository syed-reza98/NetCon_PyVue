from flask_jwt_extended import create_access_token, create_refresh_token
from models.user import User, db
from models.role import Role
from datetime import datetime, timedelta

class AuthService:
    def register_user(self, username, email, password, role_name='user'):
        # Check if user already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return {
                'success': False,
                'message': 'Username or email already exists'
            }
        
        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        # Assign role
        role = Role.query.filter_by(name=role_name).first()
        if role:
            new_user.roles.append(role)
        
        # Save to database
        db.session.add(new_user)
        db.session.commit()
        
        return {
            'success': True,
            'message': 'User registered successfully'
        }
    
    def login_user(self, username_or_email, password):
        # Find user by username or email
        user = User.query.filter((User.username == username_or_email) | 
                                (User.email == username_or_email)).first()
        
        # Check if user exists and password is correct
        if not user or not user.check_password(password):
            return {
                'success': False,
                'message': 'Invalid credentials'
            }
        
        # Generate tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return {
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'roles': [role.name for role in user.roles]
            }
        }
    
    def get_user_by_id(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return None
        
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'roles': [role.name for role in user.roles]
        }
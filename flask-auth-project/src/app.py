from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from controllers.auth_controller import auth_controller
from controllers.ej_controller import ej_controller
from config import Config
from models.user import db
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)
CORS(app)

# Register the controllers
app.register_blueprint(auth_controller, url_prefix='/api/auth')
app.register_blueprint(ej_controller, url_prefix='/api/ej')

# Create the database tables if they don't exist
with app.app_context():
    # Handle SQLite database path correctly
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if '/' in db_path:  # Only create directory if there's a path component
            directory = os.path.dirname(db_path)
            if directory:  # Check if directory is not empty
                os.makedirs(directory, exist_ok=True)
    
    db.create_all()
    
    # Import models for database creation
    from models.role import Role
    from models.permission import Permission
    
    # Create default roles if they don't exist
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin', description='Administrator with full access')
        db.session.add(admin_role)
    
    user_role = Role.query.filter_by(name='user').first()
    if not user_role:
        user_role = Role(name='user', description='Regular user with limited access')
        db.session.add(user_role)
    
    # Create default permissions if they don't exist
    if not Permission.query.filter_by(name='read').first():
        read_perm = Permission(name='read', description='Can read data')
        db.session.add(read_perm)
    
    if not Permission.query.filter_by(name='write').first():
        write_perm = Permission(name='write', description='Can write data')
        db.session.add(write_perm)
    
    if not Permission.query.filter_by(name='admin').first():
        admin_perm = Permission(name='admin', description='Has admin privileges')
        db.session.add(admin_perm)
    
    db.session.commit()

if __name__ == '__main__':
    app.run(port=5000, debug=True)
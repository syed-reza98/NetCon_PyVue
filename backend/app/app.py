from flask import Flask
from flask_cors import CORS
from controllers.ej_controller import ej_controller  # Corrected import
from controllers.auth_controller import auth_controller
from flask_sqlalchemy import SQLAlchemy
from models import db  # Import db from models

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
CORS(app)

# Register the ej controller blueprint
app.register_blueprint(ej_controller, url_prefix='/api/ej')

app.register_blueprint(auth_controller, url_prefix='/api')
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(port=5000)
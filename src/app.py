from flask import Flask
from flask_cors import CORS
from controllers.ej_controller import ej_controller  # Corrected import
from controllers.auth_controller import auth_controller

app = Flask(__name__)
CORS(app)

# Register the ej controller blueprint
app.register_blueprint(ej_controller, url_prefix='/api/ej')

app.register_blueprint(auth_controller, url_prefix='/api')
if __name__ == '__main__':
    app.run(port=5000)
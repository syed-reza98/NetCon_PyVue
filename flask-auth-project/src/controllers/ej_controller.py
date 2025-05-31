from flask import Blueprint, request, jsonify
from services.ej_service import EJService
from services.auth_service import AuthService
from flask_jwt_extended import jwt_required, get_jwt_identity

ej_controller = Blueprint('ej_controller', __name__)
ej_service = EJService()
auth_service = AuthService()

@ej_controller.route('/hello', methods=['GET'])
@jwt_required()
def hello():
    current_user = get_jwt_identity()
    return jsonify({"message": f"Hello, {current_user}!"}), 200

@ej_controller.route('/load_logs', methods=['POST'])
@jwt_required()
def load_logs():
    file_paths = request.json.get('file_paths', [])
    if not file_paths:
        return jsonify({"error": "No file paths provided"}), 400
    log_contents = ej_service.load_logs(file_paths)
    df_all_transactions = ej_service.process_transactions(log_contents)
    return jsonify(df_all_transactions.to_dict(orient='records')), 200

@ej_controller.route('/api/transactions', methods=['POST'])
@jwt_required()
def process_transactions():
    # Implementation for processing transactions
    pass

@ej_controller.route('/api/merge', methods=['POST'])
@jwt_required()
def merge_files():
    # Implementation for merging files
    pass

@ej_controller.route('/api/save', methods=['POST'])
@jwt_required()
def save_to_csv():
    # Implementation for saving to CSV
    pass
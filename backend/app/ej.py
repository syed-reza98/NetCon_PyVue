from flask import Blueprint, request, jsonify
from services.ej_service import EJService

ej_controller = Blueprint('ej_controller', __name__)
ej_service = EJService()

@ej_controller.route('/api/transactions', methods=['POST'])
def process_transactions():
    file_paths = request.json.get('file_paths', [])
    if not file_paths:
        return jsonify({"error": "No file paths provided"}), 400

    try:
        df_all_transactions = ej_service.process_transactions(file_paths)
        return jsonify(df_all_transactions.to_dict(orient='records')), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ej_controller.route('/api/merge', methods=['POST'])
def merge_files():
    file_paths = request.json.get('file_paths', [])
    if not file_paths:
        return jsonify({"error": "No file paths provided"}), 400

    try:
        merged_output_path = ej_service.merge_files(file_paths)
        return jsonify({"merged_file": merged_output_path}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ej_controller.route('/api/save', methods=['POST'])
def save_to_csv():
    filtered_data = request.json.get('filtered_data', None)
    if filtered_data is None:
        return jsonify({"error": "No data provided"}), 400

    try:
        save_path = ej_service.save_to_csv(filtered_data)
        return jsonify({"saved_file": save_path}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
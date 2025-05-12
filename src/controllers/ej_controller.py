from flask import Blueprint, request, jsonify
import logging
import json
from services.ej_service import EJService

ej_controller = Blueprint('ej_controller', __name__)
ej_service = EJService()

@ej_controller.route('/hello', methods=['GET'])
def hello():
    return jsonify(message="Hello from EJ!"), 200

@ej_controller.route('/load_logs', methods=['POST'])
def load_logs():
    # file_paths = request.json.get('file_paths', [])
    # if not file_paths:
    #     return jsonify({"error": "No file paths provided"}), 400
    # log_contents = ej_service.load_logs(file_paths)
    # df_all_transactions = ej_service.process_transactions(log_contents)
    # # return jsonify(log_contents), 200
    # return jsonify(df_all_transactions.to_dict(orient='records')), 200
    
    if ej_service.is_trial_active():
        # return jsonify({"error": "Trial period has expired"}), 403

        """Handles multiple file uploads, extracts transactions, and returns JSON"""

        if 'files' not in request.files:
            return jsonify({"error": "No files provided"}), 400

        uploaded_files = request.files.getlist("files")
        log_contents = {}

        try:
            # Read file contents properly
            for file in uploaded_files:
                content = file.read().decode("utf-8", errors="ignore")  # Fix encoding issues
                lines = content.splitlines()  # Ensure proper line splitting
                log_contents[file.filename] = lines
                logging.info(f"Received File: {file.filename}, Size: {len(content)} characters, {len(lines)} lines")

            # Use the optimized transaction processing method
            try:
                all_transactions = ej_service.process_transactions_optimized(log_contents)
                # Convert to DataFrame for compatibility with existing code
                import pandas as pd
                df_all_transactions = pd.DataFrame(all_transactions)
            except Exception as e:
                logging.error(f"Error processing transactions: {e}")
                return jsonify({"error": f"Error processing transactions: {str(e)}"}), 500

            if df_all_transactions.empty:
                print("No transactions extracted!")
                return jsonify({"error": "No transactions extracted"}), 200  

            # Filter out transactions where all key fields are empty
            valid_transactions = df_all_transactions[
                df_all_transactions[['timestamp', 'card_number', 'transaction_type', 'amount']].notna().any(axis=1)
            ]

            if valid_transactions.empty:
                print("No valid transactions found after filtering!")
                return jsonify({"error": "No valid transactions found"}), 200

            # Convert to JSON-friendly format
            transactions_json = valid_transactions.fillna("").to_dict(orient="records")

            # Debugging: Print a small sample before returning
            print("Total Valid Transactions Extracted:", len(transactions_json))
            print(json.dumps(transactions_json[:5], indent=4))  # Fix: json module now imported

            return jsonify({"transactions": transactions_json}), 200  # Send only valid transactions
        except Exception as e:
            print(f"ERROR: {str(e)}")  # Print the error in logs
            return jsonify({"error": str(e)}), 500
    else:
        print("Trial period has expired")
        # "Trial period has expired.", "Please contact Networld Technology Limited to extend your Trial."
        # return jsonify({"error": "Trial period has expired"}), 403
        return jsonify({"error": "Trial period has expired", "message": "Please contact Networld Technology Limited to extend your Trial."}), 403


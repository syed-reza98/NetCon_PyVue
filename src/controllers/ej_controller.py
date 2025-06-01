from flask import Blueprint, request, jsonify
import logging
import json
from services.ej_service import EJService
from models import db, Transaction

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
                print(f"Received File: {file.filename}, Size: {len(content)} characters, {len(lines)} lines")  # Debugging

            df_all_transactions = ej_service.process_transactions(log_contents)

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

            # Save transactions to the database
            for tx in transactions_json:
                transaction = Transaction(
                    transaction_id=tx.get('transaction_id'),
                    timestamp=tx.get('timestamp'),
                    card_number=tx.get('card_number'),
                    transaction_type=tx.get('transaction_type'),
                    retract=tx.get('retract'),
                    no_notes_dispensed=tx.get('no_notes_dispensed'),
                    notes_dispensed_unknown=tx.get('notes_dispensed_unknown'),
                    amount=tx.get('amount'),
                    response_code=tx.get('response_code'),
                    authentication=tx.get('authentication'),
                    pin_entry=tx.get('pin_entry'),
                    notes_dispensed=tx.get('notes_dispensed'),
                    notes_dispensed_count=tx.get('notes_dispensed_count'),
                    notes_dispensed_t1=tx.get('notes_dispensed_t1'),
                    notes_dispensed_t2=tx.get('notes_dispensed_t2'),
                    notes_dispensed_t3=tx.get('notes_dispensed_t3'),
                    notes_dispensed_t4=tx.get('notes_dispensed_t4'),
                    dispensed_t1=tx.get('dispensed_t1'),
                    dispensed_t2=tx.get('dispensed_t2'),
                    dispensed_t3=tx.get('dispensed_t3'),
                    dispensed_t4=tx.get('dispensed_t4'),
                    status=tx.get('status'),
                    stan=tx.get('stan'),
                    terminal=tx.get('terminal'),
                    account_number=tx.get('account_number'),
                    transaction_number=tx.get('transaction_number'),
                    cash_dispensed=tx.get('cash_dispensed'),
                    cash_rejected=tx.get('cash_rejected'),
                    cash_remaining=tx.get('cash_remaining'),
                    number_of_total_inserted_notes=tx.get('Number of Total Inserted Notes'),
                    note_count_bdt500=tx.get('Note_Count_BDT500'),
                    note_count_bdt1000=tx.get('Note_Count_BDT1000'),
                    bdt500_abox=tx.get('BDT500_ABOX'),
                    bdt500_type1=tx.get('BDT500_TYPE1'),
                    bdt500_type2=tx.get('BDT500_TYPE2'),
                    bdt500_type3=tx.get('BDT500_TYPE3'),
                    bdt500_type4=tx.get('BDT500_TYPE4'),
                    bdt500_retract=tx.get('BDT500_RETRACT'),
                    bdt500_reject=tx.get('BDT500_REJECT'),
                    bdt500_retract2=tx.get('BDT500_RETRACT2'),
                    bdt1000_abox=tx.get('BDT1000_ABOX'),
                    bdt1000_type1=tx.get('BDT1000_TYPE1'),
                    bdt1000_type2=tx.get('BDT1000_TYPE2'),
                    bdt1000_type3=tx.get('BDT1000_TYPE3'),
                    bdt1000_type4=tx.get('BDT1000_TYPE4'),
                    bdt1000_retract=tx.get('BDT1000_RETRACT'),
                    bdt1000_reject=tx.get('BDT1000_REJECT'),
                    bdt1000_retract2=tx.get('BDT1000_RETRACT2'),
                    unknown_type4=tx.get('UNKNOWN_TYPE4'),
                    unknown_retract=tx.get('UNKNOWN_RETRACT'),
                    unknown_reject=tx.get('UNKNOWN_REJECT'),
                    unknown_retract2=tx.get('UNKNOWN_RETRACT2'),
                    total_abox=tx.get('TOTAL_ABOX'),
                    total_type1=tx.get('TOTAL_TYPE1'),
                    total_type2=tx.get('TOTAL_TYPE2'),
                    total_type3=tx.get('TOTAL_TYPE3'),
                    total_type4=tx.get('TOTAL_TYPE4'),
                    total_retract=tx.get('TOTAL_RETRACT'),
                    total_reject=tx.get('TOTAL_REJECT'),
                    total_retract2=tx.get('TOTAL_RETRACT2'),
                    result=tx.get('result'),
                    scenario=tx.get('scenario'),
                    retract_type1=tx.get('retract_type1'),
                    retract_type2=tx.get('retract_type2'),
                    retract_type3=tx.get('retract_type3'),
                    retract_type4=tx.get('retract_type4'),
                    total_retracted_notes=tx.get('total_retracted_notes'),
                    deposit_retract_100=tx.get('deposit_retract_100'),
                    deposit_retract_500=tx.get('deposit_retract_500'),
                    deposit_retract_1000=tx.get('deposit_retract_1000'),
                    deposit_retract_unknown=tx.get('deposit_retract_unknown'),
                    total_deposit_retracted=tx.get('total_deposit_retracted'),
                    file_name=tx.get('file_name'),
                    ej_log=str(tx.get('ej_log')) if tx.get('ej_log') is not None else None
                )
                db.session.add(transaction)
            db.session.commit()

            # Debugging: Print a small sample before returning
            print("Total Valid Transactions Extracted:", len(transactions_json))
            print(json.dumps(transactions_json[:5], indent=4))  # Fix: json module now imported

            return jsonify({"transactions": transactions_json}), 200  # Send only valid transactions
        except Exception as e:
            logging.error("An error occurred while processing the request", exc_info=True)  # Log the error with stack trace
            return jsonify({"error": "An internal error occurred"}), 500
    else:
        print("Trial period has expired")
        # "Trial period has expired.", "Please contact Networld Technology Limited to extend your Trial."
        # return jsonify({"error": "Trial period has expired"}), 403
        return jsonify({"error": "Trial period has expired", "message": "Please contact Networld Technology Limited to extend your Trial."}), 403


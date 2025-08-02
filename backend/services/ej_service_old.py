from flask import jsonify, request
import logging
import pandas as pd
from pathlib import Path
import concurrent.futures
import re
import datetime

# Configure logging for tracking progress and debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EJService:
    def __init__(self):
        self.transaction_id_pattern = re.compile(r"\*\d+\*")
        self.timestamp_pattern = re.compile(r"DATE (\d{2}-\d{2}-\d{2})\s+TIME (\d{2}:\d{2}:\d{2})")
        self.card_pattern = re.compile(r"CARD:\s+(\d+\*+\d+)")
        self.amount_pattern = re.compile(r"BDT ([\d,]+.\d{2})")
        self.response_code_pattern = re.compile(r"RESPONSE CODE\s+:\s+(\d+)")
        self.notes_pattern = re.compile(r"DISPENSED\s+([\d\s]+)")
        self.stan_terminal_pattern = re.compile(r"(\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2})\s+(\d+)\s+(\w+)")
        self.account_pattern = re.compile(r"ACCOUNT NBR.\s+:\s+(\d+)")
        self.transaction_number_pattern = re.compile(r"TRN. NBR\s+:\s+(\d+)")
        self.cash_totals_pattern = re.compile(r"(DISPENSED|REJECTED|REMAINING)\s+([\d\s]+)")
        self.diposit_complete_pattern = re.compile(r'CIM-DEPOSIT COMPLETED(.*)')
        self.val_pattern = re.compile(r'VAL:\s+(\d{3})')

        self.notes_dispensed_count_pattern = re.compile(r"(COUNT|NOTES PRESENTED)\s+(\d+),(\d+),(\d+),(\d+)")

        self.retract_count_pattern = re.compile(r"COUNT\s+(\d+),(\d+),(\d+),(\d+)")

        self.deposit_notes_pattern = re.compile(r"(\d+) BDT X\s+(\d+) =")
        self.void_notes_pattern = re.compile(r"VOID NOTES RETRACTED:(\d+)")
        # Function to detect scenario type
        self.EJ_SCENARIOS = {
                "successful_deposit": re.compile(r"CIM-DEPOSIT COMPLETED.*?VAL:\s*\d+.*?RESPONSE CODE\s*:\s*000", re.DOTALL),
                # "host_timeout": re.compile(r"HOST TX TIMEOUT.*?UNSUCCESSFUL CASH DEPOSIT TRANSACTION", re.DOTALL),
                "deposit_retract": re.compile(r"CASHIN RETRACT STARTED.*?BILLS RETRACTED", re.DOTALL),
                "successful_withdrawal": re.compile(r"(?=.*WITHDRAWAL)(?=.*RESPONSE CODE\s*:\s*000)(?=.*NOTES TAKEN).*", re.DOTALL),
                "withdrawal_retracted": re.compile(r"WITHDRAWAL.*?RETRACT OPERATION.*?NOTES RETRACTED", re.DOTALL),
                "withdrawal_power_loss": re.compile(r"WITHDRAWAL.*?POWER INTERRUPTION DURING DISPENSE", re.DOTALL),
                "transaction_canceled_480": re.compile(r"TRANSACTION CANCELED.*?RESPONSE CODE\s*:\s*480", re.DOTALL),
        }

    def is_trial_active(self):
        """
        Check if the trial period is active based on the start date and duration.
        """
        trial_start_date = datetime.datetime(2026, 5, 6)
        trial_duration = 15
        return datetime.datetime.today() < trial_start_date + datetime.timedelta(days=trial_duration)

    def load_logs(self, file_paths):
        log_contents = {}

        def load_single_file(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    lines = file.readlines()
                    return file_path, lines
            except Exception as e:
                logging.error(f'Error reading file {file_path}: {e}')
                return file_path, None

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(load_single_file, file_paths)
            log_contents = {file_path: lines for file_path, lines in results if lines}

        return log_contents


    def process_transactions(self, log_contents):
        all_transactions = []

        def process_single_file(file_path, lines):
            transactions = self.segment_transactions(lines)
            
            # Extract transaction details from each transaction
            structured_transactions = [self.extract_transaction_details(tx) for tx in transactions]

            for tx_data in structured_transactions:
                tx_data["file_name"] = Path(file_path).name
                all_transactions.append(tx_data)
            logging.info(f'Processed transactions from file: {file_path}')

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_single_file, file_path, lines) for file_path, lines in log_contents.items()]
            concurrent.futures.wait(futures)

        return pd.DataFrame(all_transactions)

    def segment_transactions(self, lines):
        current_transaction = []
        in_transaction = False
        previous_line = None
        for line in lines:
            if "*TRANSACTION START*" in line or "*CARDLESS TRANSACTION START*" in line:
                in_transaction = True
                if current_transaction:
                    yield current_transaction
                current_transaction = [previous_line, line] if previous_line else [line]
            elif "TRANSACTION END" in line and in_transaction:
                current_transaction.append(line)
                yield current_transaction
                in_transaction = False
                current_transaction = []
            elif in_transaction:
                current_transaction.append(line)
            previous_line = line
        logging.info(f"Segmented {len(lines)} lines into transactions")

    def detect_scenario(self, transaction):
        """Detect the scenario type from a transaction log"""
        # Convert transaction list to a single string for pattern matching
        transaction_text = '\n'.join(transaction) if isinstance(transaction, list) else transaction
        
        for scenario, pattern in self.EJ_SCENARIOS.items():
            if pattern.search(transaction_text):
                return scenario
        return "unknown_scenario"

    def extract_transaction_details(self, transaction):
        transaction_data = {
            "transaction_id": None, 
            "timestamp": None, 
            "card_number": None,
            "transaction_type": None, 
            "retract": 'No', 
            "no_notes_dispensed": None,
            "notes_dispensed_unknown": None, 
            "amount": None, 
            "response_code": None,
            "authentication": False, 
            "pin_entry": False, 
            "notes_dispensed": None,
            "notes_dispensed_count": None,
            "notes_dispensed_t1": None, 
            "notes_dispensed_t2": None, 
            "notes_dispensed_t3": None, 
            "notes_dispensed_t4": None,
            "dispensed_t1": None, 
            "dispensed_t2": None, 
            "dispensed_t3": None, 
            "dispensed_t4": None,
            "status": "No Status", 
            "stan": None, 
            "terminal": None, 
            "account_number": None,
            "transaction_number": None, 
            "cash_dispensed": None, 
            "cash_rejected": None,
            "cash_remaining": None,
            'Number of Total Inserted Notes': None,
            'Note_Count_BDT500': None,
            'Note_Count_BDT1000': None,
            'BDT500_ABOX': None,
            'BDT500_TYPE1': None,
            'BDT500_TYPE2': None,
            'BDT500_TYPE3': None,
            'BDT500_TYPE4': None,
            'BDT500_RETRACT': None,
            'BDT500_REJECT': None,
            'BDT500_RETRACT2': None,
            'BDT1000_ABOX': None,
            'BDT1000_TYPE1': None,
            'BDT1000_TYPE2': None,
            'BDT1000_TYPE3': None,
            'BDT1000_TYPE4': None,
            'BDT1000_RETRACT': None,
            'BDT1000_REJECT': None,
            'BDT1000_RETRACT2': None,
            'UNKNOWN_TYPE4': None,
            'UNKNOWN_RETRACT': None,
            'UNKNOWN_REJECT': None,
            'UNKNOWN_RETRACT2': None,
            'TOTAL_ABOX': None,
            'TOTAL_TYPE1': None,
            'TOTAL_TYPE2': None,
            'TOTAL_TYPE3': None,
            'TOTAL_TYPE4': None,
            'TOTAL_RETRACT': None,
            'TOTAL_REJECT': None,
            'TOTAL_RETRACT2': None,
            'result': None,
            "scenario": "Unknown",  # Add scenario field
            "retract_type1": None,
            "retract_type2": None,
            "retract_type3": None,
            "retract_type4": None,
            "total_retracted_notes": None,
            "deposit_retract_100": None,
            "deposit_retract_500": None,
            "deposit_retract_1000": None,
            "deposit_retract_unknown": None,
            "total_deposit_retracted": None,
        }
        for i, line in enumerate(transaction):
            line = line.strip()
            logging.debug(f"Processing line: {line}")
            # Extract transaction ID from the previous line if available
            if "*TRANSACTION START*" in line and i > 0:
                tx_id_line = transaction[i - 1].strip()
                tx_id_match = self.transaction_id_pattern.search(tx_id_line)
                if tx_id_match:
                    transaction_data["transaction_id"] = tx_id_match.group().strip('*')

            # Extract timestamp
            if "DATE" in line and "TIME" in line:
                timestamp_match = self.timestamp_pattern.search(line)
                if timestamp_match:
                    date, time = timestamp_match.groups()
                    transaction_data["timestamp"] = f"{date} {time}"

            # Extract card number
            if "CARD: " in line:
                card_match = self.card_pattern.search(line)
                if card_match:
                    transaction_data["card_number"] = card_match.group(1)

            # Determine transaction type
            if "CIM-DEPOSIT ACTIVATED" in line:
                transaction_data["transaction_type"] = "Deposit"
            elif "WITHDRAWAL" in line:
                transaction_data["transaction_type"] = "Withdrawal"
            elif "BALANCE INQUIRY" in line:
                transaction_data["transaction_type"] = "Balance Inquiry"
            elif "PIN CHANGE" in line:
                transaction_data["transaction_type"] = "PIN Change"
            elif "AUTHENTICATION" in line:
                transaction_data["transaction_type"] = "Authentication"

            # Check for retract
            if re.search(r"E\*5", line):
                transaction_data["retract"] = "Yes"

            # Check for no notes dispensed
            if re.search(r"E\*2|E\*4", line):
                transaction_data["no_notes_dispensed"] = "Yes"

            # Check for notes dispensed unknown
            if re.search(r"E\*3", line):
                transaction_data["notes_dispensed_unknown"] = "Yes"

            # Extract transaction amount
            if "TRN. AMOUNT" in line:
                amount_match = self.amount_pattern.search(line)
                if amount_match:
                    transaction_data["amount"] = amount_match.group(1)

            # Extract response code
            if "RESPONSE CODE" in line:
                response_code_match = self.response_code_pattern.search(line)
                if response_code_match:
                    transaction_data["response_code"] = response_code_match.group(1)

            # Check for authentication
            if "AUTHENTICATION" in line:
                transaction_data["authentication"] = True

            # Check for PIN entry
            if "PIN ENTERED" in line:
                transaction_data["pin_entry"] = True

            # Extract notes dispensed
            if "DISPENSED" in line:
                notes_match = self.notes_pattern.search(line)
                if notes_match:
                    transaction_data["notes_dispensed"] = notes_match.group(1).strip()
                    transaction_data["dispensed_t1"] = transaction_data["notes_dispensed"][0:5]
                    transaction_data["dispensed_t2"] = transaction_data["notes_dispensed"][6:11]
                    transaction_data["dispensed_t3"] = transaction_data["notes_dispensed"][12:17]
                    transaction_data["dispensed_t4"] = transaction_data["notes_dispensed"][18:23]

            # Determine transaction status
            if "TRANSACTION CANCELED" in line:
                transaction_data["status"] = "Canceled"
            elif "NOTES TAKEN" in line:
                transaction_data["status"] = "Withdraw Completed"
            elif "CIM-DEPOSIT COMPLETED" in line:
                diposit_complete_match = re.search(self.diposit_complete_pattern, line)
                if diposit_complete_match:
                    result = diposit_complete_match.group(1).strip()
                    transaction_data["result"] = result
                    if result == "- ITEMS REFUNDED":
                        transaction_data["status"] = "ITEMS REFUNDED"
                    elif result == "-ITEMS REFUND FAILED":
                        transaction_data["status"] = "ITEMS REFUND FAILED"
                    else:
                        transaction_data["status"] = "Deposit Completed"
                        # transaction_data["status"] = "Deposit Completed"
                        val_line = transaction[i + 6].strip()
                        val_match = self.val_pattern.search(val_line)
                        if val_match:
                            val_value = int(val_match.group(1))
                            if val_value > 0:
                                cash_details = transaction[i + 7:i + 11]
                                denomination_details = transaction[i + 12:i + 21]
                                result = []
                                for denom_detail in denomination_details:
                                    denom_lines = denom_detail.strip().split('\n')
                                    for denom_line in denom_lines:
                                        denom_row = denom_line.split()
                                        result.append(denom_row)
                                cash_result = {}
                                for cash_detail in cash_details:
                                    # There are Two types of pattern in first 2 lines for notes data extraction. Two type of Example lines for cash_detail=transaction[i + 7:i + 11] total 4 lines are given below:
                                    # Example 1: 
                                    # BDT100-002,BDT500-003,  // 
                                    # BDT1000-003
                                    # REF: 000
                                    # REJECTS:001*(1
                                    # S

                                    # Example 2:
                                    # BDT500-001,
                                    # BDT1000-000
                                    # REF: 000
                                    # REJECTS:000*(1
                                    # S

                                    # Modify the code below to handle both cases

                                    cash_lines = cash_detail.strip().split('\n')
                                    notes_data = [cash_line.strip(',') for cash_line in cash_lines if cash_line.startswith('BDT')]
                                    for cash_item in notes_data:
                                        try:
                                            parts = cash_item.split('-')
                                            if len(parts) == 2:
                                                note, count = parts
                                                column_name = f"Note_Count_{note}"
                                                cash_result[column_name] = int(count)
                                            else:
                                                logging.error(f"Unexpected format for cash item '{cash_item}'")
                                        except ValueError as e:
                                            logging.error(f"Error processing cash item '{cash_item}': {e}")
                                            continue
                                transaction_data.update({
                                    'Number of Total Inserted Notes': val_value,
                                    'Note_Count_BDT500': cash_result.get('Note_Count_BDT500', 0),
                                    'Note_Count_BDT1000': cash_result.get('Note_Count_BDT1000', 0),
                                    'BDT500_ABOX': int(result[1][1]) if len(result) > 1 and len(result[1]) > 1 else 0,
                                    'BDT500_TYPE1': int(result[1][2]) if len(result) > 1 and len(result[1]) > 2 else 0,
                                    'BDT500_TYPE2': int(result[1][3]) if len(result) > 1 and len(result[1]) > 3 else 0,
                                    'BDT500_TYPE3': int(result[1][4]) if len(result) > 1 and len(result[1]) > 4 else 0,
                                    'BDT500_TYPE4': int(result[5][1]) if len(result) > 5 and len(result[5]) > 1 else 0,
                                    'BDT500_RETRACT': int(result[5][2]) if len(result) > 5 and len(result[5]) > 2 else 0,
                                    'BDT500_REJECT': int(result[5][3]) if len(result) > 5 and len(result[5]) > 3 else 0,
                                    'BDT500_RETRACT2': int(result[5][4]) if len(result) > 5 and len(result[5]) > 4 else 0,
                                    'BDT1000_ABOX': int(result[2][1]) if len(result) > 2 and len(result[2]) > 1 else 0,
                                    'BDT1000_TYPE1': int(result[2][2]) if len(result) > 2 and len(result[2]) > 2 else 0,
                                    'BDT1000_TYPE2': int(result[2][3]) if len(result) > 2 and len(result[2]) > 3 else 0,
                                    'BDT1000_TYPE3': int(result[2][4]) if len(result) > 2 and len(result[2]) > 4 else 0,
                                    'BDT1000_TYPE4': int(result[6][1]) if len(result) > 6 and len(result[6]) > 1 else 0,
                                    'BDT1000_RETRACT': int(result[6][2]) if len(result) > 6 and len(result[6]) > 2 else 0,
                                    'BDT1000_REJECT': int(result[6][3]) if len(result) > 6 and len(result[6]) > 3 else 0,
                                    'BDT1000_RETRACT2': int(result[6][4]) if len(result) > 6 and len(result[6]) > 4 else 0,
                                    'UNKNOWN_TYPE4': int(result[7][1]) if len(result) > 7 and len(result[7]) > 1 and result[7][0] == 'UNKNOWN' else 0,
                                    'UNKNOWN_RETRACT': int(result[7][2]) if len(result) > 7 and len(result[7]) > 2 and result[7][0] == 'UNKNOWN' else 0,
                                    'UNKNOWN_REJECT': int(result[7][3]) if len(result) > 7 and len(result[7]) > 3 and result[7][0] == 'UNKNOWN' else 0,
                                    'UNKNOWN_RETRACT2': int(result[7][4]) if len(result) > 7 and len(result[7]) > 4 and result[7][0] == 'UNKNOWN' else 0,
                                    'TOTAL_ABOX': int(result[3][1]) if len(result) > 3 and len(result[3]) > 1 else 0,
                                    'TOTAL_TYPE1': int(result[3][2]) if len(result) > 3 and len(result[3]) > 2 else 0,
                                    'TOTAL_TYPE2': int(result[3][3]) if len(result) > 3 and len(result[3]) > 3 else 0,
                                    'TOTAL_TYPE3': int(result[3][4]) if len(result) > 3 and len(result[3]) > 4 else 0,
                                    'TOTAL_TYPE4': int(result[8][1]) if len(result) > 8 and len(result[8]) > 1 else (int(result[7][1]) if len(result) > 7 and len(result[7]) > 1 else 0),
                                    'TOTAL_RETRACT': int(result[8][2]) if len(result) > 8 and len(result[8]) > 2 else (int(result[7][2]) if len(result) > 7 and len(result[7]) > 2 else 0),
                                    'TOTAL_REJECT': int(result[8][3]) if len(result) > 8 and len(result[8]) > 3 else (int(result[7][3]) if len(result) > 7 and len(result[7]) > 3 else 0),
                                    'TOTAL_RETRACT2': int(result[8][4]) if len(result) > 8 and len(result[8]) > 4 else (int(result[7][4]) if len(result) > 7 and len(result[7]) > 4 else 0),
                                })

            # Extract STAN and terminal information
            if "DATE" in line and "HOUR" in line and "STAN" in line and "TERMINAL" in line:
                stan_terminal_match = self.stan_terminal_pattern.search(transaction[i + 1])
                if stan_terminal_match:
                    date, time, stan, terminal = stan_terminal_match.groups()
                    transaction_data["timestamp"] = f"{date} {time}"
                    transaction_data["stan"] = stan
                    transaction_data["terminal"] = terminal

            # Extract account number
            if "ACCOUNT NBR." in line:
                account_match = self.account_pattern.search(line)
                if account_match:
                    transaction_data["account_number"] = account_match.group(1)

            # Extract transaction number
            if "TRN. NBR" in line:
                transaction_number_match = self.transaction_number_pattern.search(line)
                if transaction_number_match:
                    transaction_data["transaction_number"] = transaction_number_match.group(1)

            # Extract cash totals
            if "DISPENSED" in line or "REJECTED" in line or "REMAINING" in line:
                cash_totals_match = self.cash_totals_pattern.search(line)
                if cash_totals_match:
                    key = cash_totals_match.group(1).lower()
                    transaction_data[f"cash_{key}"] = cash_totals_match.group(2).strip()

            # notes_dispensed_count_pattern
            # Fix this line in the extract_transaction_details method
            if "COUNT" in line or "NOTES PRESENTED" in line:
                notes_dispensed_count_match = self.notes_dispensed_count_pattern.search(line)
                if notes_dispensed_count_match:
                    transaction_data["notes_dispensed_count"] = notes_dispensed_count_match.group(1)
                    transaction_data["notes_dispensed_t1"] = notes_dispensed_count_match.group(2)
                    transaction_data["notes_dispensed_t2"] = notes_dispensed_count_match.group(3)
                    transaction_data["notes_dispensed_t3"] = notes_dispensed_count_match.group(4)
                    transaction_data["notes_dispensed_t4"] = notes_dispensed_count_match.group(5)


            transaction_data['ej_log'] = transaction
        
        transaction_data["scenario"] = self.detect_scenario(transaction)

        if transaction_data["scenario"] == "withdrawal_retracted":
            for line in transaction:
                if "COUNT" in line:
                    count_match = self.retract_count_pattern.search(line)
                    if count_match:
                        transaction_data["retract_type1"] = int(count_match.group(1))
                        transaction_data["retract_type2"] = int(count_match.group(2))
                        transaction_data["retract_type3"] = int(count_match.group(3))
                        transaction_data["retract_type4"] = int(count_match.group(4))
                        transaction_data["total_retracted_notes"] = (
                            transaction_data["retract_type1"] + 
                            transaction_data["retract_type2"] + 
                            transaction_data["retract_type3"] + 
                            transaction_data["retract_type4"]
                        )
                        break
        # Add at the end of extract_transaction_details, after the withdrawal_retracted handler

        if transaction_data["scenario"] == "deposit_retract":
            # Initialize note counts to 0
            deposit_100 = 0
            deposit_500 = 0
            deposit_1000 = 0
            unknown_retracted = 0
            
            # Process each line for note counts
            for line in transaction:
                # Check for regular notes (100, 500, 1000 BDT)
                note_match = self.deposit_notes_pattern.search(line)
                if note_match:
                    denomination = int(note_match.group(1))
                    count = int(note_match.group(2))
                    
                    if denomination == 100:
                        deposit_100 = count
                    elif denomination == 500:
                        deposit_500 = count
                    elif denomination == 1000:
                        deposit_1000 = count
                
                # Check for void notes (unknown denomination)
                void_match = self.void_notes_pattern.search(line)
                if void_match:
                    unknown_retracted = int(void_match.group(1))
            
            # Store the extracted values
            transaction_data["deposit_retract_100"] = deposit_100
            transaction_data["deposit_retract_500"] = deposit_500
            transaction_data["deposit_retract_1000"] = deposit_1000
            transaction_data["deposit_retract_unknown"] = unknown_retracted
            transaction_data["total_deposit_retracted"] = deposit_100 + deposit_500 + deposit_1000 + unknown_retracted

        # Check for Unknown scenarios
        if transaction_data["scenario"] == "Unknown":
            for line in transaction:
                # Check for regular notes (100, 500, 1000 BDT)
                note_match = self.deposit_notes_pattern.search(line)
                if note_match:
                    denomination = int(note_match.group(1))
                    count = int(note_match.group(2))
                    
                    if denomination == 100:
                        unknown_100 = count
                    elif denomination == 500:
                        unknown_500 = count
                    elif denomination == 1000:
                        unknown_1000 = count
            
            # Store the extracted values
            transaction_data["deposit_retract_100"] = unknown_100
            transaction_data["deposit_retract_500"] = unknown_500
            transaction_data["deposit_retract_1000"] = unknown_1000

        return transaction_data

    def merge_files(self, file_paths, output_path='merged_EJ_logs.txt'):
        try:
            with open(output_path, 'w', encoding='utf-8') as outfile:
                for file_path in file_paths:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read())
                            outfile.write('\n')
                    except Exception as e:
                        logging.error(f'Error reading file {file_path}: {e}')
                        return None
            logging.info(f'Merged files into {output_path}')
            return output_path
        except Exception as e:
            logging.error(f'Error merging files: {e}')
            return None
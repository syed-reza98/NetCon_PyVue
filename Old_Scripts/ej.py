import re
import pandas as pd
import logging
import concurrent.futures
from pathlib import Path
from tkinter import filedialog
import datetime

# Configure logging for tracking progress and debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

transaction_id_pattern = re.compile(r"\*\d+\*")
timestamp_pattern = re.compile(r"DATE (\d{2}-\d{2}-\d{2})\s+TIME (\d{2}:\d{2}:\d{2})")
card_pattern = re.compile(r"CARD:\s+(\d{6}\*{6}\d{4})")
amount_pattern = re.compile(r"BDT ([\d,]+.\d{2})")
response_code_pattern = re.compile(r"RESPONSE CODE\s+:\s+(\d+)")
notes_pattern = re.compile(r"DISPENSED\s+([\d\s]+)")
stan_terminal_pattern = re.compile(r"(\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2})\s+(\d+)\s+(\w+)")
account_pattern = re.compile(r"ACCOUNT NBR.\s+:\s+(\d+)")
transaction_number_pattern = re.compile(r"TRN. NBR\s+:\s+(\d+)")
cash_totals_pattern = re.compile(r"(DISPENSED|REJECTED|REMAINING)\s+([\d\s]+)")
# diposit_complete_refund_pattern = r'CIM-DEPOSIT COMPLETED - ITEMS REFUNDED'
diposit_complete_pattern = re.compile(r'CIM-DEPOSIT COMPLETED(.*)')
val_pattern = re.compile(r'VAL:\s+(\d{3})')

def is_trial_active():
    """
    Check if the trial period is active based on the start date and duration.
    """
    trial_start_date = datetime.datetime(2025, 3, 6)
    trial_duration = 15
    return datetime.datetime.today() < trial_start_date + datetime.timedelta(days=trial_duration)


def read_value_from_file(file_path):
    """
    Read a single value from a file.

    Parameters:
        file_path (str): Path to the file.

    Returns:
        str: The value read from the file.
    """
    try:
        with open(file_path, 'r') as file:
            value = file.readline().strip()
            if value == 'True':
                return True
            elif value == 'False':
                return False
            else:
                return value
    except Exception as e:
        logging.error(f"Error reading value from file {file_path}: {e}")
        return None

def load_logs(file_paths):
    """
    Load log files concurrently.

    Parameters:
        file_paths (list): List of file paths to load.

    Returns:
        dict: Dictionary with file paths as keys and file contents as values.
    """
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

def segment_transactions(lines):
    current_transaction = []
    in_transaction = False
    previous_line = None
    for line in lines:
        if "*TRANSACTION START*" in line:
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

def extract_transaction_details(transaction):
    transaction_data = {
        "transaction_id": None, "timestamp": None, "card_number": None,
        "transaction_type": None, "retract": 'No', "no_notes_dispensed": None,
        "notes_dispensed_unknown": None, "amount": None, "response_code": None,
        "authentication": False, "pin_entry": False, "notes_dispensed": None,
        "dispensed_t1": None, "dispensed_t2": None, "dispensed_t3": None, "dispensed_t4": None,
        "status": None, "stan": None, "terminal": None, "account_number": None,
        "transaction_number": None, "cash_dispensed": None, "cash_rejected": None,
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
        'result' : None,
    }
    for i, line in enumerate(transaction):
        line = line.strip()
        logging.debug(f"Processing line: {line}")
        # Extract transaction ID from the previous line if available
        if "*TRANSACTION START*" in line and i > 0:
            tx_id_line = transaction[i - 1].strip()
            tx_id_match = transaction_id_pattern.search(tx_id_line)
            if tx_id_match:
                transaction_data["transaction_id"] = tx_id_match.group().strip('*')

        # Extract timestamp
        if "DATE" in line and "TIME" in line:
            timestamp_match = timestamp_pattern.search(line)
            if timestamp_match:
                date, time = timestamp_match.groups()
                transaction_data["timestamp"] = f"{date} {time}"

        # Extract card number
        if "CARD: " in line:
            card_match = card_pattern.search(line)
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
            amount_match = amount_pattern.search(line)
            if amount_match:
                transaction_data["amount"] = amount_match.group(1)

        # Extract response code
        if "RESPONSE CODE" in line:
            response_code_match = response_code_pattern.search(line)
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
            notes_match = notes_pattern.search(line)
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
            diposit_complete_match = re.search(diposit_complete_pattern, line)
            # diposit_complete_refund_match = re.search(diposit_complete_refund_pattern, line)
            #     transaction_data["status"] = "Deposit Completed ITEMS REFUNDED"
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
                    val_match = val_pattern.search(val_line)
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
            # elif diposit_complete_refund_match:
            #     transaction_data["status"] = "Deposit Completed ITEMS REFUNDED"

        # Extract STAN and terminal information
        if "DATE" in line and "HOUR" in line and "STAN" in line and "TERMINAL" in line:
            stan_terminal_match = stan_terminal_pattern.search(transaction[i + 1])
            if stan_terminal_match:
                date, time, stan, terminal = stan_terminal_match.groups()
                transaction_data["timestamp"] = f"{date} {time}"
                transaction_data["stan"] = stan
                transaction_data["terminal"] = terminal

        # Extract account number
        if "ACCOUNT NBR." in line:
            account_match = account_pattern.search(line)
            if account_match:
                transaction_data["account_number"] = account_match.group(1)

        # Extract transaction number
        if "TRN. NBR" in line:
            transaction_number_match = transaction_number_pattern.search(line)
            if transaction_number_match:
                transaction_data["transaction_number"] = transaction_number_match.group(1)

        # Extract cash totals
        if "DISPENSED" in line or "REJECTED" in line or "REMAINING" in line:
            cash_totals_match = cash_totals_pattern.search(line)
            if cash_totals_match:
                key = cash_totals_match.group(1).lower()
                transaction_data[f"cash_{key}"] = cash_totals_match.group(2).strip()

        transaction_data['ej_log'] = transaction

    return transaction_data

def process_transactions(log_contents):
    """
    Process transactions from log contents.

    Parameters:
        log_contents (dict): Dictionary with file paths as keys and file contents as values.

    Returns:
        pd.DataFrame: DataFrame containing all processed transactions.
    """
    all_transactions = []

    def process_single_file(file_path, lines):
        transactions = segment_transactions(lines)
        structured_transactions = [extract_transaction_details(tx) for tx in transactions]
        for tx_data in structured_transactions:
            tx_data["file_name"] = Path(file_path).name
            all_transactions.append(tx_data)
        logging.info(f'Processed transactions from file: {file_path}')

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_single_file, file_path, lines) for file_path, lines in log_contents.items()]
        concurrent.futures.wait(futures)

    return pd.DataFrame(all_transactions)

def merge_files(file_paths, output_path='merged_EJ_logs.txt'):
    """
    Merge multiple log files into a single file.
    
    Parameters:
        file_paths (list): List of file paths to merge.
        output_path (str): Path to the output file.
    
    Returns:
        str: Path to the merged output file if successful, None otherwise.
    """
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

def save_to_csv(filtered_data, default_filename='filtered_transactions.csv'):
    """
    Saves filtered data to a CSV file.
    
    Parameters:
        filtered_data (pd.DataFrame): The filtered DataFrame to save.
        default_filename (str): The default filename for saving.
    """
    if filtered_data.empty:
        logging.warning('No data to save to CSV.')
        return

    save_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")],
        initialfile=default_filename
    )
    if save_path:
        filtered_data.to_csv(save_path, index=False)
        logging.info(f'Saved filtered data to {save_path}')
    else:
        logging.warning('Save operation cancelled.')

def main(file_paths):
    """
    Main processing flow.
    
    Parameters:
        file_paths (list): List of file paths to process.
    """
    log_contents = load_logs(file_paths)
    df_all_transactions = process_transactions(log_contents)
    merged_output_path = merge_files(file_paths)
    transactions_output_path = 'df_all_transactions_optimized.csv'
    df_all_transactions.to_csv(transactions_output_path, index=False)

    # Final Output Paths
    print("Merged file saved at:", merged_output_path)
    print("Transaction data saved at:", transactions_output_path)

if __name__ == "__main__":
    file_paths = ['']  # Populate this list with actual file paths
    main(file_paths)
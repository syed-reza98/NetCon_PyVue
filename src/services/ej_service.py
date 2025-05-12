from flask import jsonify, request
import logging
import pandas as pd
from pathlib import Path
import concurrent.futures
import re
import datetime
import os
import json

# Configure logging for tracking progress and debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration settings
CONFIG = {
    # Trial configuration
    "trial": {
        "start_date": datetime.datetime(2025, 5, 6),
        "duration_days": 15
    },
    # Currency denominations
    "currency": {
        "denominations": [100, 500, 1000]
    }
}

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
        # Add this pattern to your __init__ method
        self.retract_count_pattern = re.compile(r"COUNT\s+(\d+),(\d+),(\d+),(\d+)")
        # Add these patterns to your __init__ method
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
        
        Returns:
            bool: True if the current date is within the trial period, False otherwise
        """
        trial_start_date = CONFIG["trial"]["start_date"]
        trial_duration = CONFIG["trial"]["duration_days"]
        return datetime.datetime.today() < trial_start_date + datetime.timedelta(days=trial_duration)

    def load_logs(self, file_paths):
        """
        Load transaction logs from multiple files using parallel processing.
        
        Args:
            file_paths (list): List of file paths to load logs from
            
        Returns:
            dict: Dictionary with file paths as keys and file lines as values
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


    def process_transactions(self, log_contents):
        """
        Process transaction logs from multiple files in parallel.
        
        Args:
            log_contents (dict): Dictionary with file paths as keys and file lines as values
            
        Returns:
            pandas.DataFrame: Structured transaction data
        """
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

    def process_transactions_optimized(self, log_contents, batch_size=100):
        """
        Process transaction logs from multiple files with optimized performance.
        This method processes transactions in batches to improve memory efficiency.
        
        Args:
            log_contents (dict): Dictionary with file paths as keys and file lines as values
            batch_size (int): Number of transactions to process in each batch
            
        Returns:
            list: List of processed transaction data dictionaries
        """
        all_transactions = []
        processed_count = 0
        
        # Process each file
        for file_path, lines in log_contents.items():
            logging.info(f"Processing file: {file_path}")
            
            # Convert generator to a list for batching
            transactions_list = list(self.segment_transactions(lines))
            file_total = len(transactions_list)
            logging.info(f"Found {file_total} transactions in {file_path}")
            
            # Process transactions in batches
            for i in range(0, file_total, batch_size):
                batch = transactions_list[i:i + batch_size]
                batch_transactions = []
                
                # Process each transaction in the batch in parallel
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    batch_futures = {executor.submit(self.extract_transaction_details, t): t for t in batch}
                    
                    for future in concurrent.futures.as_completed(batch_futures):
                        try:
                            transaction_data = future.result()
                            if transaction_data:
                                transaction_data["file_path"] = file_path
                                batch_transactions.append(transaction_data)
                        except Exception as e:
                            logging.error(f"Error processing transaction: {e}")
                
                # Add batch transactions to the overall result
                all_transactions.extend(batch_transactions)
                processed_count += len(batch)
                logging.info(f"Progress: {processed_count} transactions processed from {file_path}")
        
        logging.info(f"Total transactions processed: {processed_count}")
        return all_transactions

    def segment_transactions(self, lines):
        """
        Segment an EJ log file into individual transactions.
        
        Args:
            lines (list): Lines from an EJ log file
            
        Yields:
            list: List of lines for each transaction
        """
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
        """
        Detect the scenario type from a transaction log.
        
        Args:
            transaction (list or str): Transaction data as a list of lines or a string
            
        Returns:
            str: Detected scenario type or 'unknown_scenario' if no match
        """
        # Convert transaction list to a single string for pattern matching
        transaction_text = '\n'.join(transaction) if isinstance(transaction, list) else transaction
        
        for scenario, pattern in self.EJ_SCENARIOS.items():
            if pattern.search(transaction_text):
                return scenario
        return "unknown_scenario"

    def extract_transaction_details(self, transaction):
        """
        Extract detailed transaction information from EJ log transaction.
        
        Args:
            transaction (list): List of strings representing a transaction
            
        Returns:
            dict: Dictionary with structured transaction data
        """
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
            transaction_data = self._extract_basic_transaction_info(transaction, i, line, transaction_data)
            transaction_data = self._extract_cash_details(line, transaction_data)

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
                        # Process deposit notes with improved error handling
                        transaction_data = self._process_deposit_notes(transaction, i, transaction_data)

            # Extract STAN and terminal information
            if "DATE" in line and "HOUR" in line and "STAN" in line and "TERMINAL" in line:
                try:
                    # Add bounds checking before accessing next line
                    if i + 1 < len(transaction):
                        stan_terminal_match = self.stan_terminal_pattern.search(transaction[i + 1])
                        if stan_terminal_match:
                            date, time, stan, terminal = stan_terminal_match.groups()
                            transaction_data["timestamp"] = f"{date} {time}"
                            transaction_data["stan"] = stan
                            transaction_data["terminal"] = terminal
                except Exception as e:
                    logging.error(f"Error extracting STAN and terminal information: {e}")

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
            transaction_data = self._process_withdrawal_retract(transaction, transaction_data)

        if transaction_data["scenario"] == "deposit_retract":
            transaction_data = self._process_deposit_retract(transaction, transaction_data)

        if transaction_data["scenario"] == "Unknown":
            transaction_data = self._process_unknown_scenario(transaction, transaction_data)

        return transaction_data

    def merge_files(self, file_paths, output_path='merged_EJ_logs.txt'):
        """
        Merge multiple EJ log files into a single file.
        
        Args:
            file_paths (list): List of file paths to merge
            output_path (str, optional): Path for the merged file. Defaults to 'merged_EJ_logs.txt'.
            
        Returns:
            str or None: Path to the merged file on success, None on failure
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

    def _process_withdrawal_retract(self, transaction, transaction_data):
        """
        Process withdrawal retract scenario and extract relevant data.
        
        Args:
            transaction (list): Transaction data as a list of lines
            transaction_data (dict): Dictionary to store extracted data
            
        Returns:
            dict: Updated transaction data
        """
        for line in transaction:
            if "COUNT" in line:
                count_match = self.retract_count_pattern.search(line)
                if count_match:
                    try:
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
                    except (ValueError, IndexError) as e:
                        logging.error(f"Error processing retract count: {e}")
                    break
        return transaction_data

    def _process_deposit_retract(self, transaction, transaction_data):
        """
        Process deposit retract scenario and extract note denominations.
        
        Args:
            transaction (list): Transaction data as a list of lines
            transaction_data (dict): Dictionary to store extracted data
            
        Returns:
            dict: Updated transaction data
        """
        # Initialize note counts to 0
        deposit_100 = 0
        deposit_500 = 0
        deposit_1000 = 0
        unknown_retracted = 0
        
        # Process each line for note counts
        for line in transaction:
            try:
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
            except (ValueError, IndexError) as e:
                logging.error(f"Error processing deposit retract line: {e}")
                continue
        
        # Store the extracted values
        transaction_data["deposit_retract_100"] = deposit_100
        transaction_data["deposit_retract_500"] = deposit_500
        transaction_data["deposit_retract_1000"] = deposit_1000
        transaction_data["deposit_retract_unknown"] = unknown_retracted
        transaction_data["total_deposit_retracted"] = deposit_100 + deposit_500 + deposit_1000 + unknown_retracted
        
        return transaction_data

    def _process_unknown_scenario(self, transaction, transaction_data):
        """
        Process unknown transaction scenario and extract available data.
        
        Args:
            transaction (list): Transaction data as a list of lines
            transaction_data (dict): Dictionary to store extracted data
            
        Returns:
            dict: Updated transaction data
        """
        # Initialize variables to avoid UnboundLocalError
        unknown_100 = 0
        unknown_500 = 0
        unknown_1000 = 0
        
        for line in transaction:
            try:
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
            except (ValueError, IndexError) as e:
                logging.error(f"Error processing unknown scenario: {e}")
                continue
        
        # Store the extracted values
        transaction_data["deposit_retract_100"] = unknown_100
        transaction_data["deposit_retract_500"] = unknown_500
        transaction_data["deposit_retract_1000"] = unknown_1000
        
        return transaction_data

    def _extract_basic_transaction_info(self, transaction, i, line, transaction_data):
        """
        Extract basic transaction information from a line.
        
        Args:
            transaction (list): Transaction data as a list of lines
            i (int): Current line index
            line (str): Current line text
            transaction_data (dict): Dictionary to store extracted data
            
        Returns:
            dict: Updated transaction data
        """
        try:
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
        except Exception as e:
            logging.error(f"Error extracting basic transaction info: {e}")
            
        return transaction_data
        
    def _extract_cash_details(self, line, transaction_data):
        """
        Extract cash details from transaction line.
        
        Args:
            line (str): Line from transaction log
            transaction_data (dict): Dictionary to store extracted data
            
        Returns:
            dict: Updated transaction data
        """
        try:
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
        except Exception as e:
            logging.error(f"Error extracting cash details: {e}")
            
        return transaction_data

    def _process_deposit_notes(self, transaction, index, transaction_data):
        """
        Process and extract information about deposited notes from transaction logs.
        
        Args:
            transaction (list): List of transaction lines
            index (int): Current index in the transaction list
            transaction_data (dict): Transaction data dictionary to update
            
        Returns:
            dict: Updated transaction data with deposit note information
        """
        try:
            # Initialize notes data if not already present
            if "notes" not in transaction_data:
                transaction_data["notes"] = {}
            
            # Process deposit notes by denomination
            for i in range(index, min(index + 10, len(transaction))):
                deposit_match = self.deposit_notes_pattern.search(transaction[i])
                if deposit_match:
                    denomination, count = deposit_match.groups()
                    denomination = int(denomination)
                    count = int(count)
                    
                    # Store deposit information by denomination
                    transaction_data["notes"][str(denomination)] = count
                    
                    # Calculate total if possible
                    if "total" not in transaction_data:
                        transaction_data["total"] = 0
                    transaction_data["total"] += denomination * count
            
            # Check for void notes
            for i in range(index, min(index + 15, len(transaction))):
                void_match = self.void_notes_pattern.search(transaction[i])
                if void_match:
                    void_count = int(void_match.group(1))
                    transaction_data["void_notes"] = void_count
        except Exception as e:
            logging.error(f"Error processing deposit notes: {e}")
            
        return transaction_data
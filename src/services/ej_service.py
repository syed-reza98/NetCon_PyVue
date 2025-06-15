"""
Improved EJ Service with enhanced error handling, logging, performance optimization, and maintainability.
Processes Electronic Journal (EJ) transaction logs from ATM systems.
"""

from flask import current_app
import logging
import pandas as pd
from pathlib import Path
import concurrent.futures
import re
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple, Generator
import hashlib
import json
from dataclasses import dataclass
from collections import defaultdict
import time

# Configure structured logging
logger = logging.getLogger(__name__)

@dataclass
class ProcessingMetrics:
    """Metrics for transaction processing"""
    files_processed: int = 0
    transactions_extracted: int = 0
    processing_time: float = 0.0
    errors: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class EJService:
    """
    Enhanced EJ Service for processing ATM transaction logs with improved
    error handling, performance, and maintainability.
    """
    
    def __init__(self):
        """Initialize the EJ Service with compiled regex patterns and configuration"""
        self._init_regex_patterns()
        self._init_scenarios()
        self._init_config()
          # Metrics tracking
        self.processing_metrics = ProcessingMetrics()
        
        logger.info("EJServiceImproved initialized successfully")

    def _init_regex_patterns(self):
        """Initialize and compile regex patterns for better performance"""
        self.patterns = {
            'transaction_id': re.compile(r"\*\d+\*"),
            'timestamp': re.compile(r"DATE (\d{2}-\d{2}-\d{2})\s+TIME (\d{2}:\d{2}:\d{2})"),
            'card': re.compile(r"CARD:\s+(\d+\*+\d+)"),
            'amount': re.compile(r"BDT ([\d,]+\.\d{2})"),
            'response_code': re.compile(r"RESPONSE CODE\s+:\s+(\d+)"),
            'notes': re.compile(r"DISPENSED\s+([\d\s]+)"),
            'stan_terminal': re.compile(r"(\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2})\s+(\d+)\s+(\w+)"),
            'account': re.compile(r"ACCOUNT NBR\.\s+:\s+(\d+)"),
            'transaction_number': re.compile(r"TRN\. NBR\s+:\s+(\d+)"),
            'cash_totals': re.compile(r"(DISPENSED|REJECTED|REMAINING)\s+([\d\s]+)"),
            'deposit_complete': re.compile(r'CIM-DEPOSIT COMPLETED(.*)'),
            'val': re.compile(r'VAL:\s+(\d{3})'),
            'notes_dispensed_count': re.compile(r"(COUNT|NOTES PRESENTED)\s+(\d+),(\d+),(\d+),(\d+)"),
            'retract_count': re.compile(r"COUNT\s+(\d+),(\d+),(\d+),(\d+)"),
            'deposit_notes': re.compile(r"(\d+) BDT X\s+(\d+) ="),
            'void_notes': re.compile(r"VOID NOTES RETRACTED:(\d+)")
        }

    def _init_scenarios(self):
        """Initialize transaction scenario patterns"""
        self.scenarios = {
            "successful_deposit": re.compile(
                r"CIM-DEPOSIT COMPLETED.*?VAL:\\s*\\d+.*?RESPONSE CODE\\s*:\\s*000", 
                re.DOTALL
            ),
            "deposit_retract": re.compile(
                r"CASHIN RETRACT STARTED.*?BILLS RETRACTED", 
                re.DOTALL
            ),
            "successful_withdrawal": re.compile(
                r"(?=.*WITHDRAWAL)(?=.*RESPONSE CODE\\s*:\\s*000)(?=.*NOTES TAKEN).*", 
                re.DOTALL
            ),
            "withdrawal_retracted": re.compile(
                r"WITHDRAWAL.*?RETRACT OPERATION.*?NOTES RETRACTED", 
                re.DOTALL
            ),
            "withdrawal_power_loss": re.compile(
                r"WITHDRAWAL.*?POWER INTERRUPTION DURING DISPENSE", 
                re.DOTALL
            ),
            "transaction_canceled_480": re.compile(
                r"TRANSACTION CANCELED.*?RESPONSE CODE\\s*:\\s*480", 
                re.DOTALL
            ),
        }

    def _init_config(self):
        """Initialize service configuration from Flask app config"""
        try:
            config = current_app.config
            self.config = {
                'trial_start_date': config.get('TRIAL_START_DATE', datetime(2025, 6, 6)),
                'trial_duration_days': config.get('TRIAL_DURATION_DAYS', 55),
                'max_workers': config.get('EJ_MAX_WORKERS', min(4, (os.cpu_count() or 1) + 1)),
                'chunk_size': config.get('EJ_CHUNK_SIZE', 1000),
                'max_file_size': config.get('EJ_MAX_FILE_SIZE', 10 * 1024 * 1024),  # 10MB
                'supported_encodings': config.get('EJ_SUPPORTED_ENCODINGS', ['utf-8', 'utf-16', 'latin-1']),
                'cache_enabled': config.get('EJ_CACHE_ENABLED', True),
                'performance_logging': config.get('EJ_PERFORMANCE_LOGGING', True)
            }
        except RuntimeError:
            # Fallback config when not in Flask app context
            logger.warning("Flask app context not available, using default configuration")
            self.config = {
                'trial_start_date': datetime(2025, 6, 6),
                'trial_duration_days': 55,
                'max_workers': 4,
                'chunk_size': 1000,
                'max_file_size': 10 * 1024 * 1024,
                'supported_encodings': ['utf-8', 'utf-16', 'latin-1'],
                'cache_enabled': True,
                'performance_logging': True
            }

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the service.
        
        Returns:
            Dictionary with health status information
        """
        try:
            # Test regex patterns
            test_line = "DATE 01-01-21 TIME 12:00:00"
            self.patterns['timestamp'].search(test_line)
            
            # Test scenario detection
            test_transaction = ["WITHDRAWAL", "RESPONSE CODE : 000", "NOTES TAKEN"]
            self.detect_scenario(test_transaction)
            
            return {
                'status': 'healthy',
                'patterns_loaded': len(self.patterns),
                'scenarios_loaded': len(self.scenarios),
                'config_loaded': bool(self.config),
                'trial_active': self.is_trial_active()
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    def is_trial_active(self) -> bool:
        """
        Check if the trial period is active based on configuration.
        
        Returns:
            True if trial is active, False otherwise
        """
        try:
            trial_start = self.config['trial_start_date']
            trial_duration = self.config['trial_duration_days']
            trial_end = trial_start + timedelta(days=trial_duration)
            
            current_time = datetime.now()
            is_active = current_time < trial_end
            
            if self.config.get('performance_logging'):
                logger.info(f"Trial check: Current={current_time}, End={trial_end}, Active={is_active}")
            
            return is_active
            
        except Exception as e:
            logger.error(f"Error checking trial status: {e}")
            return False

    def load_logs(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """
        Load log files with improved error handling and encoding detection.
        
        Args:
            file_paths: List of file paths to load
            
        Returns:
            Dictionary mapping file paths to line lists
        """
        start_time = time.time()
        log_contents = {}
        errors = []

        def load_single_file(file_path: str) -> Tuple[str, Optional[List[str]], Optional[str]]:
            """Load a single file with encoding detection"""
            try:
                # Check file size
                file_size = Path(file_path).stat().st_size
                if file_size > self.config['max_file_size']:
                    return file_path, None, f"File too large: {file_size} bytes"

                # Try different encodings
                for encoding in self.config['supported_encodings']:
                    try:
                        with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
                            lines = file.readlines()
                            logger.debug(f"Successfully loaded {file_path} with {encoding} encoding")
                            return file_path, [line.strip() for line in lines], None
                    except UnicodeDecodeError:
                        continue
                
                return file_path, None, "Unable to decode file with supported encodings"
                
            except FileNotFoundError:
                return file_path, None, "File not found"
            except PermissionError:
                return file_path, None, "Permission denied"
            except Exception as e:
                return file_path, None, f"Unexpected error: {str(e)}"

        # Load files concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config['max_workers']) as executor:
            futures = [executor.submit(load_single_file, file_path) for file_path in file_paths]
            
            for future in concurrent.futures.as_completed(futures):
                file_path, lines, error = future.result()
                
                if lines:
                    log_contents[file_path] = lines
                    logger.info(f'Successfully loaded {file_path}: {len(lines)} lines')
                else:
                    error_msg = f'Failed to load {file_path}: {error}'
                    logger.error(error_msg)
                    errors.append(error_msg)

        # Update metrics
        processing_time = time.time() - start_time
        self.processing_metrics.files_processed = len(log_contents)
        self.processing_metrics.processing_time += processing_time
        self.processing_metrics.errors.extend(errors)

        if self.config.get('performance_logging'):
            logger.info(f"Loaded {len(log_contents)} files in {processing_time:.2f}s")

        return log_contents

    def process_transactions(self, log_contents: Dict[str, List[str]]) -> pd.DataFrame:
        """
        Enhanced transaction processing with better error handling and performance.
        
        Args:
            log_contents: Dictionary mapping filenames to line lists
            
        Returns:
            DataFrame containing processed transactions
        """
        start_time = time.time()
        all_transactions = []
        processing_errors = []

        def process_single_file(file_path: str, lines: List[str]) -> Tuple[List[Dict], List[str]]:
            """Process a single file and return transactions and errors"""
            try:
                # Segment transactions
                transactions = list(self.segment_transactions(lines))
                logger.debug(f"Segmented {len(transactions)} transactions from {file_path}")
                
                # Process each transaction
                structured_transactions = []
                file_errors = []
                
                for i, transaction in enumerate(transactions):
                    try:
                        tx_data = self.extract_transaction_details(transaction)
                        tx_data["file_name"] = Path(file_path).name
                        tx_data["file_hash"] = self._generate_file_hash(file_path)
                        tx_data["transaction_index"] = i
                        structured_transactions.append(tx_data)
                    except Exception as e:
                        error_msg = f"Error processing transaction {i} in {file_path}: {str(e)}"
                        logger.error(error_msg)
                        file_errors.append(error_msg)
                
                logger.info(f'Processed {len(structured_transactions)} transactions from {file_path}')
                return structured_transactions, file_errors
                
            except Exception as e:
                error_msg = f"Error processing file {file_path}: {str(e)}"
                logger.error(error_msg)
                return [], [error_msg]

        # Process files concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config['max_workers']) as executor:
            futures = {
                executor.submit(process_single_file, file_path, lines): file_path 
                for file_path, lines in log_contents.items()
            }
            
            for future in concurrent.futures.as_completed(futures):
                file_path = futures[future]
                try:
                    structured_transactions, file_errors = future.result()
                    all_transactions.extend(structured_transactions)
                    processing_errors.extend(file_errors)
                except Exception as e:
                    error_msg = f"Future execution failed for {file_path}: {str(e)}"
                    logger.error(error_msg)
                    processing_errors.append(error_msg)

        # Create DataFrame with error handling
        try:
            df = pd.DataFrame(all_transactions) if all_transactions else pd.DataFrame()
            
            # Update metrics
            processing_time = time.time() - start_time
            self.processing_metrics.transactions_extracted = len(all_transactions)
            self.processing_metrics.processing_time += processing_time
            self.processing_metrics.errors.extend(processing_errors)
            
            if self.config.get('performance_logging'):
                logger.info(f"Processed {len(all_transactions)} transactions in {processing_time:.2f}s")
            
            return df
            
        except Exception as e:
            logger.error(f"Error creating DataFrame: {str(e)}")
            return pd.DataFrame()

    def segment_transactions(self, lines: List[str]) -> Generator[List[str], None, None]:
        """
        Segment log lines into individual transactions.
        
        Args:
            lines: List of log lines
            
        Yields:
            Lists of lines representing individual transactions
        """
        current_transaction = []
        in_transaction = False
        previous_line = None
        
        transaction_start_patterns = ["*TRANSACTION START*", "*CARDLESS TRANSACTION START*"]
        transaction_end_pattern = "TRANSACTION END"
        
        for line_num, line in enumerate(lines):
            try:
                line = line.strip()
                
                # Check for transaction start
                if any(pattern in line for pattern in transaction_start_patterns):
                    in_transaction = True
                    if current_transaction:
                        yield current_transaction
                    current_transaction = [previous_line] if previous_line else []
                    current_transaction.append(line)
                    
                # Check for transaction end
                elif transaction_end_pattern in line and in_transaction:
                    current_transaction.append(line)
                    yield current_transaction
                    in_transaction = False
                    current_transaction = []
                    
                # Add line to current transaction if we're in one
                elif in_transaction:
                    current_transaction.append(line)
                    
                previous_line = line
                
            except Exception as e:
                logger.warning(f"Error processing line {line_num}: {str(e)}")
                continue
          # Yield last transaction if incomplete
        if current_transaction and in_transaction:
            logger.warning("Incomplete transaction found at end of file")
            yield current_transaction

    def detect_scenario(self, transaction: List[str]) -> str:
        """
        Detect the scenario type from a transaction log with improved matching.
        
        Args:
            transaction: List of transaction lines or single string
            
        Returns:
            Detected scenario name or "unknown_scenario"
        """
        try:
            # Convert transaction to string if needed
            if isinstance(transaction, list):
                transaction_text = '\n'.join(transaction)
            else:
                transaction_text = transaction
            
            # Check each scenario pattern
            for scenario, pattern in self.scenarios.items():
                try:
                    if pattern.search(transaction_text):
                        logger.debug(f"Detected scenario: {scenario}")
                        return scenario
                except Exception as e:
                    logger.warning(f"Error matching scenario {scenario}: {str(e)}")
                    continue
            
            return "unknown_scenario"
            
        except Exception as e:
            logger.error(f"Error in scenario detection: {str(e)}")
            return "error_scenario"

    def extract_transaction_details(self, transaction: List[str]) -> Dict[str, Any]:
        """
        Extract transaction details with enhanced error handling and validation.
        
        Args:
            transaction: List of transaction lines
            
        Returns:
            Dictionary containing extracted transaction data
        """
        # Initialize transaction data with comprehensive default values
        transaction_data = self._init_transaction_data()
        
        try:
            # Process each line
            for i, line in enumerate(transaction):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    self._process_transaction_line(line, i, transaction, transaction_data)
                except Exception as e:
                    logger.debug(f"Error processing line {i}: '{line}' - {str(e)}")
                    continue
            
            # Post-process transaction data
            self._post_process_transaction(transaction, transaction_data)
            
            # Add metadata
            transaction_data['processing_timestamp'] = datetime.now(timezone.utc).isoformat()
            transaction_data['ej_log'] = transaction
            
            return transaction_data
            
        except Exception as e:
            logger.error(f"Error extracting transaction details: {str(e)}")
            # Return minimal transaction data with error info
            transaction_data.update({
                'extraction_error': str(e),
                'ej_log': transaction
            })
            return transaction_data

    def _init_transaction_data(self) -> Dict[str, Any]:
        """Initialize transaction data dictionary with default values"""
        return {
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
            'TOTAL_ABOX': None,
            'TOTAL_TYPE1': None,
            'TOTAL_TYPE2': None,
            'TOTAL_TYPE3': None,
            'TOTAL_TYPE4': None,
            'TOTAL_RETRACT': None,
            'TOTAL_REJECT': None,
            'TOTAL_RETRACT2': None,
            'result': None,
            "scenario": "Unknown",
            "retract_type1": None,
            "retract_type2": None,
            "retract_type3": None,
            "retract_type4": None,
            "total_retracted_notes": None,
            "deposit_retract_100": None,            "deposit_retract_500": None,
            "deposit_retract_1000": None,
            "deposit_retract_unknown": None,
            "total_deposit_retracted": None,
        }

    def _process_transaction_line(self, line: str, line_index: int, 
                                transaction: List[str], transaction_data: Dict[str, Any]):
        """Process individual transaction line to extract relevant data"""
        
        # Extract transaction ID from previous line if available
        if "*TRANSACTION START*" in line and line_index > 0:
            prev_line = transaction[line_index - 1].strip()
            tx_id_match = self.patterns['transaction_id'].search(prev_line)
            if tx_id_match:
                transaction_data["transaction_id"] = tx_id_match.group().strip('*')

        # Extract timestamp
        if "DATE" in line and "TIME" in line:
            timestamp_match = self.patterns['timestamp'].search(line)
            if timestamp_match:
                date_str, time_str = timestamp_match.groups()
                transaction_data["timestamp"] = f"{date_str} {time_str}"

        # Extract card number
        if "CARD:" in line:
            card_match = self.patterns['card'].search(line)
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
            amount_match = self.patterns['amount'].search(line)
            if amount_match:
                transaction_data["amount"] = amount_match.group(1)

        # Extract response code
        if "RESPONSE CODE" in line:
            response_match = self.patterns['response_code'].search(line)
            if response_match:
                transaction_data["response_code"] = response_match.group(1)

        # Check for authentication
        if "AUTHENTICATION" in line:
            transaction_data["authentication"] = True

        # Check for PIN entry
        if "PIN ENTERED" in line:
            transaction_data["pin_entry"] = True

        # Extract notes dispensed
        if "DISPENSED" in line:
            notes_match = self.patterns['notes'].search(line)
            if notes_match:
                transaction_data["notes_dispensed"] = notes_match.group(1).strip()
                notes_str = transaction_data["notes_dispensed"]
                if len(notes_str) >= 23:
                    transaction_data["dispensed_t1"] = notes_str[0:5]
                    transaction_data["dispensed_t2"] = notes_str[6:11]
                    transaction_data["dispensed_t3"] = notes_str[12:17]
                    transaction_data["dispensed_t4"] = notes_str[18:23]

        # Determine transaction status
        if "TRANSACTION CANCELED" in line:
            transaction_data["status"] = "Canceled"
        elif "NOTES TAKEN" in line:
            transaction_data["status"] = "Withdraw Completed"
        elif "CIM-DEPOSIT COMPLETED" in line:
            deposit_complete_match = re.search(self.patterns['deposit_complete'], line)
            if deposit_complete_match:
                result = deposit_complete_match.group(1).strip()
                transaction_data["result"] = result
                if result == "- ITEMS REFUNDED":
                    transaction_data["status"] = "ITEMS REFUNDED"
                elif result == "-ITEMS REFUND FAILED":
                    transaction_data["status"] = "ITEMS REFUND FAILED"
                else:
                    transaction_data["status"] = "Deposit Completed"
                    # Handle VAL processing and deposit details
                    self._process_deposit_completion(line_index, transaction, transaction_data)

        # Extract STAN and terminal info
        if "DATE" in line and "HOUR" in line and "STAN" in line and "TERMINAL" in line:
            if line_index + 1 < len(transaction):
                stan_terminal_match = self.patterns['stan_terminal'].search(transaction[line_index + 1])
                if stan_terminal_match:
                    date, time, stan, terminal = stan_terminal_match.groups()
                    transaction_data["timestamp"] = f"{date} {time}"
                    transaction_data["stan"] = stan
                    transaction_data["terminal"] = terminal

        # Extract account number
        if "ACCOUNT NBR." in line:
            account_match = self.patterns['account'].search(line)
            if account_match:
                transaction_data["account_number"] = account_match.group(1)

        # Extract transaction number
        if "TRN. NBR" in line:
            transaction_number_match = self.patterns['transaction_number'].search(line)
            if transaction_number_match:
                transaction_data["transaction_number"] = transaction_number_match.group(1)

        # Extract cash totals
        cash_types = ["DISPENSED", "REJECTED", "REMAINING"]
        for cash_type in cash_types:
            if cash_type in line:
                cash_match = self.patterns['cash_totals'].search(line)
                if cash_match:
                    key = cash_match.group(1).lower()
                    transaction_data[f"cash_{key}"] = cash_match.group(2).strip()

        # Extract notes dispensed count
        if "COUNT" in line or "NOTES PRESENTED" in line:
            notes_count_match = self.patterns['notes_dispensed_count'].search(line)
            if notes_count_match:
                transaction_data["notes_dispensed_count"] = notes_count_match.group(1)
                transaction_data["notes_dispensed_t1"] = self._safe_int(notes_count_match.group(2))
                transaction_data["notes_dispensed_t2"] = self._safe_int(notes_count_match.group(3))
                transaction_data["notes_dispensed_t3"] = self._safe_int(notes_count_match.group(4))
                transaction_data["notes_dispensed_t4"] = self._safe_int(notes_count_match.group(5))

    def _post_process_transaction(self, transaction: List[str], transaction_data: Dict[str, Any]):
        """Post-process transaction data after line-by-line extraction"""
        
        # Detect scenario
        transaction_data["scenario"] = self.detect_scenario(transaction)
        
        # Process scenario-specific data
        if transaction_data["scenario"] == "withdrawal_retracted":
            self._process_withdrawal_retracted(transaction, transaction_data)
        elif transaction_data["scenario"] == "deposit_retract":
            self._process_deposit_retract(transaction, transaction_data)
        elif transaction_data["scenario"] == "unknown_scenario":
            self._process_unknown_scenario(transaction, transaction_data)

    def _process_withdrawal_retracted(self, transaction: List[str], transaction_data: Dict[str, Any]):
        """Process withdrawal retracted scenario specific data"""
        for line in transaction:
            if "COUNT" in line:
                count_match = self.patterns['retract_count'].search(line)
                if count_match:
                    transaction_data["retract_type1"] = self._safe_int(count_match.group(1))
                    transaction_data["retract_type2"] = self._safe_int(count_match.group(2))
                    transaction_data["retract_type3"] = self._safe_int(count_match.group(3))
                    transaction_data["retract_type4"] = self._safe_int(count_match.group(4))
                    
                    # Calculate total
                    total = sum(filter(None, [
                        transaction_data["retract_type1"],
                        transaction_data["retract_type2"],
                        transaction_data["retract_type3"],
                        transaction_data["retract_type4"]
                    ]))
                    transaction_data["total_retracted_notes"] = total
                    break

    def _process_deposit_retract(self, transaction: List[str], transaction_data: Dict[str, Any]):
        """Process deposit retract scenario specific data"""
        deposit_100 = 0
        deposit_500 = 0
        deposit_1000 = 0
        unknown_retracted = 0
        
        for line in transaction:
            # Check for regular notes
            note_match = self.patterns['deposit_notes'].search(line)
            if note_match:
                denomination = self._safe_int(note_match.group(1))
                count = self._safe_int(note_match.group(2))
                
                if denomination == 100:
                    deposit_100 = count or 0
                elif denomination == 500:
                    deposit_500 = count or 0
                elif denomination == 1000:
                    deposit_1000 = count or 0
            
            # Check for void notes
            void_match = self.patterns['void_notes'].search(line)
            if void_match:
                unknown_retracted = self._safe_int(void_match.group(1)) or 0
        
        # Store extracted values
        transaction_data.update({
            "deposit_retract_100": deposit_100,
            "deposit_retract_500": deposit_500,
            "deposit_retract_1000": deposit_1000,
            "deposit_retract_unknown": unknown_retracted,
            "total_deposit_retracted": deposit_100 + deposit_500 + deposit_1000 + unknown_retracted
        })

    def _process_unknown_scenario(self, transaction: List[str], transaction_data: Dict[str, Any]):
        """Process unknown scenario data"""
        unknown_100 = 0
        unknown_500 = 0
        unknown_1000 = 0
        
        for line in transaction:
            note_match = self.patterns['deposit_notes'].search(line)
            if note_match:
                denomination = self._safe_int(note_match.group(1))
                count = self._safe_int(note_match.group(2))
                
                if denomination == 100:
                    unknown_100 = count or 0
                elif denomination == 500:
                    unknown_500 = count or 0
                elif denomination == 1000:
                    unknown_1000 = count or 0
        
        transaction_data.update({
            "deposit_retract_100": unknown_100,
            "deposit_retract_500": unknown_500,
            "deposit_retract_1000": unknown_1000
        })

    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to integer"""
        if value is None:
            return None
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return None

    def _generate_file_hash(self, file_path: str) -> str:
        """Generate hash for file identification"""
        try:
            return hashlib.md5(str(file_path).encode()).hexdigest()[:8]
        except Exception:
            return "unknown"

    def merge_files(self, file_paths: List[str], output_path: str = 'merged_EJ_logs.txt') -> Optional[str]:
        """
        Merge multiple log files into a single file with improved error handling.
        
        Args:
            file_paths: List of input file paths
            output_path: Output file path
            
        Returns:
            Output file path if successful, None otherwise
        """
        start_time = time.time()
        
        try:
            merged_lines = 0
            with open(output_path, 'w', encoding='utf-8') as outfile:
                for file_path in file_paths:
                    try:
                        # Use the same encoding detection as load_logs
                        for encoding in self.config['supported_encodings']:
                            try:
                                with open(file_path, 'r', encoding=encoding) as infile:
                                    content = infile.read()
                                    outfile.write(content)
                                    outfile.write('\\n')
                                    merged_lines += content.count('\\n')
                                    logger.debug(f"Merged {file_path} using {encoding} encoding")
                                    break
                            except UnicodeDecodeError:
                                continue
                        else:
                            logger.error(f'Unable to decode {file_path} with supported encodings')
                            continue
                            
                    except Exception as e:
                        logger.error(f'Error reading file {file_path}: {e}')
                        continue
            
            processing_time = time.time() - start_time
            logger.info(f'Merged {len(file_paths)} files into {output_path} ({merged_lines} lines) in {processing_time:.2f}s')
            return output_path
            
        except Exception as e:
            logger.error(f'Error merging files: {e}')
            return None

    def get_processing_metrics(self) -> ProcessingMetrics:
        """Get current processing metrics"""
        return self.processing_metrics

    def reset_metrics(self):
        """Reset processing metrics"""
        self.processing_metrics = ProcessingMetrics()
        logger.info("Processing metrics reset")

    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize DataFrame memory usage and data types.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Optimized DataFrame
        """
        if df.empty:
            return df
        
        try:
            # Convert object columns to category where appropriate
            for col in df.select_dtypes(include=['object']).columns:
                if df[col].nunique() / len(df) < 0.5:  # Less than 50% unique values
                    df[col] = df[col].astype('category')
            
            # Optimize numeric columns
            for col in df.select_dtypes(include=['int64']).columns:
                df[col] = pd.to_numeric(df[col], downcast='integer')
            
            for col in df.select_dtypes(include=['float64']).columns:
                df[col] = pd.to_numeric(df[col], downcast='float')
            
            logger.info(f"DataFrame optimized: {df.memory_usage(deep=True).sum() // 1024} KB")
            return df
            
        except Exception as e:
            logger.error(f"Error optimizing DataFrame: {e}")
            return df

    def _process_deposit_completion(self, line_index: int, transaction: List[str], transaction_data: Dict[str, Any]):
        """Process deposit completion details including VAL and note count processing"""
        try:
            # Look for VAL line (typically 6 lines after the CIM-DEPOSIT COMPLETED line)
            if line_index + 6 < len(transaction):
                val_line = transaction[line_index + 6].strip()
                val_match = self.patterns['val'].search(val_line)
                if val_match:
                    val_value = int(val_match.group(1))
                    if val_value > 0:
                        # Process cash details (lines 7-10 after completion)
                        cash_details = transaction[line_index + 7:line_index + 11]
                        denomination_details = transaction[line_index + 12:line_index + 21]
                        
                        # Process denomination details
                        result = []
                        for denom_detail in denomination_details:
                            denom_lines = denom_detail.strip().split('\n')
                            for denom_line in denom_lines:
                                denom_row = denom_line.split()
                                result.append(denom_row)
                        
                        # Process cash details
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
                                        logger.error(f"Unexpected format for cash item '{cash_item}'")
                                except ValueError as e:
                                    logger.error(f"Error processing cash item '{cash_item}': {e}")
                                    continue
                        
                        # Update transaction data with detailed deposit information
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
        except Exception as e:
            logger.error(f"Error processing deposit completion: {str(e)}")

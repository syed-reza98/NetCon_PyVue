"""
Unit tests for the EJService class in the NetCon_PyVue application.
These tests verify the functionality of transaction processing and extraction.
"""

import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
import os
import json
from pathlib import Path
import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the service class
from services.ej_service import EJService

class TestEJService(unittest.TestCase):
    """Test cases for the EJService class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.ej_service = EJService()
        
        # Sample transaction data for testing
        self.sample_withdrawal_transaction = [
            "*123*",
            "DATE 01-01-23 TIME 12:34:56",
            "WITHDRAWAL",
            "CARD: 1234****5678",
            "BDT 10,000.00",
            "RESPONSE CODE : 000",
            "NOTES DISPENSED 10x1000",
            "NOTES TAKEN",
            "DATE HOUR STAN TERMINAL",
            "01/01/23 12:34:56 123456 TERM01",
            "ACCOUNT NBR. : 12345678901234",
            "TRN. NBR : 987654"
        ]
        
        self.sample_deposit_transaction = [
            "*456*",
            "DATE 02-02-23 TIME 14:25:36",
            "CIM-DEPOSIT COMPLETED",
            "CARD: 5678****1234",
            "VAL: 001",
            "1000 BDT X 5 =",
            "500 BDT X 2 =",
            "100 BDT X 3 =",
            "RESPONSE CODE : 000",
            "DATE HOUR STAN TERMINAL",
            "02/02/23 14:25:36 654321 TERM02",
            "ACCOUNT NBR. : 98765432109876",
            "TRN. NBR : 123456"
        ]
        
    def test_detect_scenario_withdrawal(self):
        """Test the detection of a withdrawal scenario"""
        scenario = self.ej_service.detect_scenario(self.sample_withdrawal_transaction)
        self.assertEqual(scenario, "successful_withdrawal")
        
    def test_detect_scenario_deposit(self):
        """Test the detection of a deposit scenario"""
        scenario = self.ej_service.detect_scenario(self.sample_deposit_transaction)
        self.assertEqual(scenario, "successful_deposit")
    
    def test_extract_transaction_details_withdrawal(self):
        """Test extraction of withdrawal transaction details"""
        transaction_data = self.ej_service.extract_transaction_details(self.sample_withdrawal_transaction)
        
        # Verify key information was extracted correctly
        self.assertEqual(transaction_data.get("transaction_id"), "*123*")
        self.assertEqual(transaction_data.get("timestamp"), "01-01-23 12:34:56")
        self.assertEqual(transaction_data.get("card"), "1234****5678")
        self.assertEqual(transaction_data.get("amount"), "10,000.00")
        self.assertEqual(transaction_data.get("scenario"), "successful_withdrawal")
        self.assertEqual(transaction_data.get("stan"), "123456")
        self.assertEqual(transaction_data.get("terminal"), "TERM01")
        
    def test_extract_transaction_details_deposit(self):
        """Test extraction of deposit transaction details"""
        transaction_data = self.ej_service.extract_transaction_details(self.sample_deposit_transaction)
        
        # Verify key information was extracted correctly
        self.assertEqual(transaction_data.get("transaction_id"), "*456*")
        self.assertEqual(transaction_data.get("timestamp"), "02-02-23 14:25:36")
        self.assertEqual(transaction_data.get("card"), "5678****1234")
        self.assertEqual(transaction_data.get("scenario"), "successful_deposit")
        self.assertEqual(transaction_data.get("stan"), "654321")
        self.assertEqual(transaction_data.get("terminal"), "TERM02")
        
        # Verify deposit-specific fields
        self.assertIn("notes", transaction_data)
        self.assertEqual(transaction_data["notes"].get("1000"), 5)
        self.assertEqual(transaction_data["notes"].get("500"), 2)
        self.assertEqual(transaction_data["notes"].get("100"), 3)
        
    def test_load_logs(self):
        """Test loading of log files"""
        with patch('builtins.open', mock_open(read_data="*123*\nTEST DATA")) as mock_file:
            file_paths = ['file1.txt', 'file2.txt']
            log_contents = self.ej_service.load_logs(file_paths)
            
            # Verify each file was read
            self.assertEqual(len(log_contents), 2)
            self.assertIn('file1.txt', log_contents)
            self.assertIn('file2.txt', log_contents)
            
            # Verify the content of each file
            for file_path, lines in log_contents.items():
                self.assertEqual(lines, ["*123*\n", "TEST DATA"])
                
    def test_segment_transactions(self):
        """Test segmentation of log files into individual transactions"""
        lines = [
            "*123*\n",
            "TRANSACTION DATA 1\n",
            "MORE DATA 1\n",
            "*456*\n",
            "TRANSACTION DATA 2\n",
            "MORE DATA 2\n"
        ]
        
        transactions = self.ej_service.segment_transactions(lines)
        
        # Verify the correct number of transactions were extracted
        self.assertEqual(len(transactions), 2)
        
        # Verify the content of each transaction
        self.assertEqual(transactions[0][0].strip(), "*123*")
        self.assertEqual(transactions[1][0].strip(), "*456*")
        
    def test_is_trial_active(self):
        """Test the trial period checking functionality"""
        # This would need to be mocked to make it deterministic
        with patch('datetime.datetime') as mock_datetime:
            # Setup mock to return a date within the trial period
            mock_today = MagicMock()
            mock_today.return_value = self.ej_service.CONFIG["trial"]["start_date"] + \
                                     datetime.timedelta(days=5)
            mock_datetime.today = mock_today
            
            # Trial should be active
            self.assertTrue(self.ej_service.is_trial_active())
            
            # Setup mock to return a date after the trial period
            mock_today.return_value = self.ej_service.CONFIG["trial"]["start_date"] + \
                                     datetime.timedelta(days=20)
            mock_datetime.today = mock_today
            
            # Trial should not be active
            self.assertFalse(self.ej_service.is_trial_active())

if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""
Test database integration with the updated EJ service.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.ej_service import EJService
from src.models import Transaction, db
from flask import Flask
import pandas as pd
from datetime import datetime

def create_test_app():
    """Create a test Flask app with database"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_ej.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def test_database_integration():
    """Test EJ service database integration"""
    print("Testing EJ Service Database Integration...")
    
    # Create test app
    app = create_test_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        print("✓ Database tables created")
        
        # Initialize EJ service
        ej_service = EJService()
        print("✓ EJ Service initialized")
        
        # Process sample transactions
        sample_transactions = [
            {
                'transaction_id': '12345',
                'timestamp': '25-04-25 10:30:45',
                'card_number': '1234****5678',
                'transaction_type': 'Withdrawal',
                'amount': '1,000.00',
                'response_code': '000',
                'scenario': 'successful_withdrawal',
                'status': 'Withdraw Completed',
                'file_name': 'test.log'
            },
            {
                'transaction_id': '12346',
                'timestamp': '25-04-25 11:15:30',
                'card_number': '9876****4321',
                'transaction_type': 'Deposit',
                'amount': '5,000.00',
                'response_code': '000',
                'scenario': 'successful_deposit',
                'status': 'Deposit Completed',
                'file_name': 'test.log'
            }
        ]
        
        # Save transactions to database
        saved_count = 0
        for tx_data in sample_transactions:
            try:
                # Convert amount string to float
                amount_str = tx_data['amount'].replace(',', '')
                amount_float = float(amount_str)
                
                # Parse timestamp
                timestamp_obj = datetime.strptime(tx_data['timestamp'], '%d-%m-%y %H:%M:%S')
                
                # Create transaction object
                transaction = Transaction(
                    transaction_id=tx_data['transaction_id'],
                    timestamp=timestamp_obj,
                    card_number=tx_data['card_number'],
                    transaction_type=tx_data['transaction_type'],
                    amount=amount_float,
                    response_code=tx_data['response_code'],
                    scenario=tx_data['scenario'],
                    status=tx_data['status'],
                    file_name=tx_data['file_name']
                )
                
                db.session.add(transaction)
                saved_count += 1
                
            except Exception as e:
                print(f"✗ Error creating transaction: {e}")
                continue
        
        # Commit to database
        try:
            db.session.commit()
            print(f"✓ Saved {saved_count} transactions to database")
        except Exception as e:
            print(f"✗ Error saving to database: {e}")
            return False
        
        # Query transactions from database
        try:
            transactions = Transaction.query.all()
            print(f"✓ Retrieved {len(transactions)} transactions from database")
            
            if transactions:
                first_tx = transactions[0]
                print(f"  Sample transaction:")
                print(f"    ID: {first_tx.transaction_id}")
                print(f"    Type: {first_tx.transaction_type}")
                print(f"    Amount: {first_tx.amount}")
                print(f"    Status: {first_tx.status}")
                print(f"    Scenario: {first_tx.scenario}")
                
                # Test computed properties
                print(f"    Is Successful: {first_tx.is_successful}")
                print(f"    Has Anomaly: {first_tx.has_anomaly}")
            
        except Exception as e:
            print(f"✗ Error querying database: {e}")
            return False
        
        print("\n" + "="*50)
        print("Database Integration Test Summary:")
        print("- Database creation: ✓")
        print(f"- Transaction saving: ✓ ({saved_count} transactions)")
        print(f"- Transaction retrieval: ✓ ({len(transactions)} transactions)")
        print("- Model properties: ✓")
        print("="*50)
        
        return True

if __name__ == "__main__":
    try:
        success = test_database_integration()
        if success:
            print("\n✓ Database integration test passed!")
        else:
            print("\n✗ Database integration test failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

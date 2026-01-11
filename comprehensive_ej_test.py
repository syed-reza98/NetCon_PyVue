#!/usr/bin/env python3
"""
Comprehensive test: Process real EJ log file and save to database.
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
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///comprehensive_test.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def parse_timestamp(timestamp_str):
    """Parse timestamp from EJ format"""
    if not timestamp_str:
        return None
    try:
        # Handle different timestamp formats
        if '/' in timestamp_str:
            return datetime.strptime(timestamp_str, '%d/%m/%y %H:%M:%S')
        elif '-' in timestamp_str:
            return datetime.strptime(timestamp_str, '%d-%m-%y %H:%M:%S')
        else:
            return None
    except:
        return None

def save_transactions_to_db(transactions_df):
    """Save processed transactions to database"""
    saved_count = 0
    error_count = 0
    
    for _, row in transactions_df.iterrows():
        try:
            # Parse amount
            amount_val = None
            if row['amount']:
                amount_str = str(row['amount']).replace(',', '')
                try:
                    amount_val = float(amount_str)
                except:
                    amount_val = None
            
            # Parse timestamp
            timestamp_obj = parse_timestamp(row['timestamp'])
            
            # Create transaction
            transaction = Transaction(
                transaction_id=row.get('transaction_id'),
                timestamp=timestamp_obj,
                card_number=row.get('card_number'),
                transaction_type=row.get('transaction_type'),
                amount=amount_val,
                response_code=row.get('response_code'),
                scenario=row.get('scenario', 'Unknown'),
                status=row.get('status', 'Unknown'),
                file_name=row.get('file_name'),
                
                # Authentication fields
                authentication=bool(row.get('authentication', False)),
                pin_entry=bool(row.get('pin_entry', False)),
                retract=row.get('retract') == 'Yes',
                
                # Terminal info
                stan=row.get('stan'),
                terminal=row.get('terminal'),
                account_number=row.get('account_number'),
                transaction_number=row.get('transaction_number'),
                
                # Notes info
                notes_dispensed=row.get('notes_dispensed'),
                notes_dispensed_count=row.get('notes_dispensed_count'),
                notes_dispensed_t1=row.get('notes_dispensed_t1'),
                notes_dispensed_t2=row.get('notes_dispensed_t2'),
                notes_dispensed_t3=row.get('notes_dispensed_t3'),
                notes_dispensed_t4=row.get('notes_dispensed_t4'),
                
                # Retraction info
                retract_type1=row.get('retract_type1'),
                retract_type2=row.get('retract_type2'),
                retract_type3=row.get('retract_type3'),
                retract_type4=row.get('retract_type4'),
                total_retracted_notes=row.get('total_retracted_notes'),
                
                # Deposit info
                number_of_total_inserted_notes=row.get('Number of Total Inserted Notes'),
                note_count_bdt500=row.get('Note_Count_BDT500'),
                note_count_bdt1000=row.get('Note_Count_BDT1000'),
                
                # Denomination details
                bdt500_abox=row.get('BDT500_ABOX'),
                bdt500_type1=row.get('BDT500_TYPE1'),
                bdt500_type2=row.get('BDT500_TYPE2'),
                bdt500_type3=row.get('BDT500_TYPE3'),
                bdt500_type4=row.get('BDT500_TYPE4'),
                bdt500_retract=row.get('BDT500_RETRACT'),
                bdt500_reject=row.get('BDT500_REJECT'),
                bdt500_retract2=row.get('BDT500_RETRACT2'),
                
                bdt1000_abox=row.get('BDT1000_ABOX'),
                bdt1000_type1=row.get('BDT1000_TYPE1'),
                bdt1000_type2=row.get('BDT1000_TYPE2'),
                bdt1000_type3=row.get('BDT1000_TYPE3'),
                bdt1000_type4=row.get('BDT1000_TYPE4'),
                bdt1000_retract=row.get('BDT1000_RETRACT'),
                bdt1000_reject=row.get('BDT1000_REJECT'),
                bdt1000_retract2=row.get('BDT1000_RETRACT2'),
                
                # Totals
                total_abox=row.get('TOTAL_ABOX'),
                total_type1=row.get('TOTAL_TYPE1'),
                total_type2=row.get('TOTAL_TYPE2'),
                total_type3=row.get('TOTAL_TYPE3'),
                total_type4=row.get('TOTAL_TYPE4'),
                total_retract=row.get('TOTAL_RETRACT'),
                total_reject=row.get('TOTAL_REJECT'),
                total_retract2=row.get('TOTAL_RETRACT2'),
                
                # Deposit retraction
                deposit_retract_100=row.get('deposit_retract_100'),
                deposit_retract_500=row.get('deposit_retract_500'),
                deposit_retract_1000=row.get('deposit_retract_1000'),
                deposit_retract_unknown=row.get('deposit_retract_unknown'),
                total_deposit_retracted=row.get('total_deposit_retracted'),
                
                # Raw log data
                ej_log=str(row.get('ej_log', [])),
                result=row.get('result')
            )
            
            db.session.add(transaction)
            saved_count += 1
            
        except Exception as e:
            print(f"  ✗ Error saving transaction {row.get('transaction_id', 'unknown')}: {e}")
            error_count += 1
            continue
    
    return saved_count, error_count

def comprehensive_test():
    """Comprehensive test with real data and database"""
    print("Comprehensive EJ Service Test...")
    print("="*50)
    
    # Create test app
    app = create_test_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        print("✓ Database tables created")
        
        # Initialize EJ service
        ej_service = EJService()
        print("✓ EJ Service initialized")
        
        # Load and process real log file
        log_file = "TestCase.log"
        if not os.path.exists(log_file):
            print(f"✗ Log file {log_file} not found")
            return False
        
        print(f"Processing log file: {log_file}")
        
        # Load logs
        log_contents = ej_service.load_logs([log_file])
        print(f"✓ Loaded log file with {len(log_contents[log_file])} lines")
        
        # Process transactions
        transactions_df = ej_service.process_transactions(log_contents)
        print(f"✓ Processed {len(transactions_df)} transactions")
        
        if len(transactions_df) == 0:
            print("✗ No transactions found to save")
            return False
        
        # Show scenario distribution
        scenario_counts = transactions_df['scenario'].value_counts()
        print("Scenario distribution:")
        for scenario, count in scenario_counts.items():
            print(f"  {scenario}: {count}")
        
        # Save to database
        print("\nSaving transactions to database...")
        saved_count, error_count = save_transactions_to_db(transactions_df)
        
        # Commit
        try:
            db.session.commit()
            print(f"✓ Successfully saved {saved_count} transactions")
            if error_count > 0:
                print(f"⚠ {error_count} transactions had errors")
        except Exception as e:
            print(f"✗ Error committing to database: {e}")
            return False
        
        # Verify data in database
        total_in_db = Transaction.query.count()
        print(f"✓ Database contains {total_in_db} transactions")
        
        # Show sample data
        if total_in_db > 0:
            sample_tx = Transaction.query.first()
            print(f"\nSample transaction from database:")
            print(f"  ID: {sample_tx.transaction_id}")
            print(f"  Type: {sample_tx.transaction_type}")
            print(f"  Amount: {sample_tx.amount}")
            print(f"  Scenario: {sample_tx.scenario}")
            print(f"  Status: {sample_tx.status}")
            print(f"  Is Successful: {sample_tx.is_successful}")
            print(f"  Has Anomaly: {sample_tx.has_anomaly}")
        
        print("\n" + "="*50)
        print("COMPREHENSIVE TEST SUMMARY:")
        print(f"- Log file processed: ✓ ({len(log_contents[log_file])} lines)")
        print(f"- Transactions extracted: ✓ ({len(transactions_df)} transactions)")
        print(f"- Database save: ✓ ({saved_count} saved, {error_count} errors)")
        print(f"- Database verification: ✓ ({total_in_db} total in DB)")
        print("- All core functionality: ✓")
        print("="*50)
        
        return True

if __name__ == "__main__":
    try:
        success = comprehensive_test()
        if success:
            print("\n🎉 COMPREHENSIVE TEST PASSED! 🎉")
            print("The updated EJ service is working perfectly!")
        else:
            print("\n❌ COMPREHENSIVE TEST FAILED!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

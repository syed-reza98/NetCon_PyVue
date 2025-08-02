#!/usr/bin/env python3
"""
Test the updated EJ service with real log file data.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.ej_service import EJService

def test_real_log_processing():
    """Test EJ service with real log file"""
    print("Testing EJ Service with real log file...")
    
    # Initialize the service
    ej_service = EJService()
    print("✓ EJ Service initialized successfully")
    
    # Test loading the log file
    log_file = "TestCase.log"
    if not os.path.exists(log_file):
        print(f"✗ Log file {log_file} not found")
        return False
    
    try:
        # Load logs
        log_contents = ej_service.load_logs([log_file])
        print(f"✓ Loaded log file with {len(log_contents[log_file])} lines")
        
        # Process transactions
        transactions_df = ej_service.process_transactions(log_contents)
        print(f"✓ Processed {len(transactions_df)} transactions")
        
        if len(transactions_df) > 0:
            print(f"\nFirst transaction sample:")
            first_transaction = transactions_df.iloc[0]
            key_fields = [
                'transaction_id', 'timestamp', 'card_number', 'transaction_type',
                'amount', 'response_code', 'scenario', 'status'
            ]
            
            for field in key_fields:
                if field in first_transaction and first_transaction[field] is not None:
                    print(f"  {field}: {first_transaction[field]}")
            
            # Show scenario distribution
            scenario_counts = transactions_df['scenario'].value_counts()
            print(f"\nScenario distribution:")
            for scenario, count in scenario_counts.items():
                print(f"  {scenario}: {count}")
        
        print("\n" + "="*50)
        print("Real Log Processing Test Summary:")
        print(f"- Log file loaded: ✓ ({len(log_contents[log_file])} lines)")
        print(f"- Transactions extracted: ✓ ({len(transactions_df)} transactions)")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"✗ Error processing log file: {e}")
        return False

if __name__ == "__main__":
    try:
        success = test_real_log_processing()
        if success:
            print("\n✓ Real log processing test passed!")
        else:
            print("\n✗ Real log processing test failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        sys.exit(1)

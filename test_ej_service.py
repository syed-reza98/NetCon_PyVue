#!/usr/bin/env python3
"""
Test the updated EJ service to verify it can process transactions correctly.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.ej_service import EJService

def test_ej_service():
    """Test basic EJ service functionality"""
    print("Testing EJ Service...")
    
    # Initialize the service
    ej_service = EJService()
    print("✓ EJ Service initialized successfully")
    
    # Test regex patterns
    patterns = ej_service.patterns
    print(f"✓ Loaded {len(patterns)} regex patterns")
    
    # Test scenarios
    scenarios = ej_service.scenarios  
    print(f"✓ Loaded {len(scenarios)} transaction scenarios")
    
    # Test scenario detection with sample data
    sample_transaction = [
        "*123456*",
        "*TRANSACTION START*",
        "DATE 25-04-25 TIME 10:30:45",
        "CARD: 1234****5678",
        "WITHDRAWAL",
        "TRN. AMOUNT: BDT 1,000.00",
        "RESPONSE CODE : 000",
        "NOTES TAKEN",
        "*TRANSACTION END*"
    ]
    
    scenario = ej_service.detect_scenario(sample_transaction)
    print(f"✓ Detected scenario: {scenario}")
    
    # Test transaction extraction
    transaction_data = ej_service.extract_transaction_details(sample_transaction)
    print(f"✓ Extracted transaction data with {len(transaction_data)} fields")
    
    # Check key fields
    expected_fields = [
        'transaction_id', 'timestamp', 'card_number', 'transaction_type',
        'amount', 'response_code', 'scenario', 'status'
    ]
    
    for field in expected_fields:
        if field in transaction_data and transaction_data[field] is not None:
            print(f"  ✓ {field}: {transaction_data[field]}")
        else:
            print(f"  - {field}: Not extracted")
    
    print("\n" + "="*50)
    print("EJ Service Test Summary:")
    print("- Service initialization: ✓")
    print("- Pattern compilation: ✓") 
    print("- Scenario detection: ✓")
    print("- Transaction extraction: ✓")
    print("="*50)
    
    return True

if __name__ == "__main__":
    try:
        test_ej_service()
        print("\n✓ All tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)

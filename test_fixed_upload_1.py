#!/usr/bin/env python3
"""
Test file upload with fixed backend to verify transaction processing
"""
import requests
import json
from pathlib import Path

# API base URL
BASE_URL = "http://127.0.0.1:5000"

def test_registration_and_upload():
    """Test user registration, login, and file upload with transaction processing"""
    
    print("=== Testing Fixed File Upload and Transaction Processing ===")
    
    # 1. Register a test user
    print("\n1. Registering test user...")
    register_data = {
        "email": "testfixed@example.com",
        "username": "testfixed",
        "password": "TestPass123!"    }
    
    register_response = requests.post(f"{BASE_URL}/api/register", json=register_data)
    print(f"Registration: {register_response.status_code}")
    if register_response.status_code == 201:
        print("✓ User registered successfully")
    elif register_response.status_code == 400:
        print("! User may already exist, continuing with login...")
    else:
        print(f"✗ Registration failed: {register_response.text}")
        return
    
    # 2. Login to get JWT token
    print("\n2. Logging in...")
    login_data = {
        "email": "testfixed@example.com",
        "password": "TestPass123!"
    }
    
    login_response = requests.post(f"{BASE_URL}/api/login", json=login_data)
    print(f"Login: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"✗ Login failed: {login_response.text}")
        return
    
    token = login_response.json().get('access_token')
    print("✓ Login successful, token received")
    
    # 3. Create a simple test EJ file
    print("\n3. Creating test EJ file...")
    test_file_path = Path("test_transaction.003")
    test_content = """
********************
*TRANSACTION START*
********************
\\*12345*\\
DATE 15-06-25  TIME 08:45:30
CARD: 1234****5678
WITHDRAWAL
BDT 1,000.00
RESPONSE CODE    : 000
NOTES PRESENTED    5  0  0  0
STAN: 123456
TERMINAL: ATM001
ACCOUNT NBR. : 987654321
TRN. NBR : 789012
NOTES TAKEN
DISPENSED    1000  0  0  0
********************
*TRANSACTION END*
********************
    """
    
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    print(f"✓ Test file created: {test_file_path}")
    
    # 4. Upload and process the file
    print("\n4. Uploading and processing file...")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    with open(test_file_path, 'rb') as f:
        files = {'files': (test_file_path.name, f, 'application/octet-stream')}
        upload_response = requests.post(f"{BASE_URL}/api/ej/load_logs", files=files, headers=headers)
    
    print(f"Upload: {upload_response.status_code}")
    
    if upload_response.status_code == 200:
        response_data = upload_response.json()
        print("✓ File uploaded and processed successfully!")
        print(f"  - Files processed: {response_data.get('files_processed', 'N/A')}")
        print(f"  - Transactions extracted: {response_data.get('transactions_extracted', 'N/A')}")
        print(f"  - Database saved: {response_data.get('database_saved', 'N/A')}")
        print(f"  - Processing time: {response_data.get('processing_time', 'N/A')}s")
    else:
        print(f"✗ Upload failed: {upload_response.status_code}")
        print(f"Response: {upload_response.text}")
    
    # 5. Test getting transactions
    print("\n5. Testing transaction retrieval...")
    get_response = requests.get(f"{BASE_URL}/api/ej/transactions", headers=headers)
    print(f"Get transactions: {get_response.status_code}")
    
    if get_response.status_code == 200:
        transactions = get_response.json()
        print(f"✓ Retrieved {len(transactions.get('transactions', []))} transactions")
        if transactions.get('transactions'):
            first_tx = transactions['transactions'][0]
            print(f"  - Sample transaction ID: {first_tx.get('transaction_id')}")
            print(f"  - Transaction type: {first_tx.get('transaction_type')}")
            print(f"  - Amount: {first_tx.get('amount')}")
            print(f"  - Status: {first_tx.get('status')}")
    else:
        print(f"✗ Failed to retrieve transactions: {get_response.text}")
    
    # 6. Clean up
    print("\n6. Cleaning up...")
    try:
        test_file_path.unlink()
        print("✓ Test file cleaned up")
    except FileNotFoundError:
        print("! Test file not found for cleanup")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    test_registration_and_upload()

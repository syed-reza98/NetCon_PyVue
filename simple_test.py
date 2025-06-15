#!/usr/bin/env python3
"""
Simple test to verify our database fixes work
"""
import requests
import json

# Test registration
print("Testing registration...")
data = {
    "email": "finaltest@example.com", 
    "username": "finaltest",
    "password": "TestPass123!",
    "repassword": "TestPass123!"
}

response = requests.post("http://127.0.0.1:5000/api/register", json=data)
print(f"Registration response: {response.status_code}")
print(f"Response body: {response.text}")

if response.status_code in [200, 201]:
    print("✓ Registration successful")
elif response.status_code in [400, 409]:
    print("! User already exists, proceeding with login")
else:
    print("✗ Registration failed")
    print(f"Error: {response.text}")
    # Don't exit, try login anyway

# Test login
print("\nTesting login...")
login_data = {
    "email": "finaltest@example.com",
    "password": "TestPass123!"
}

login_response = requests.post("http://127.0.0.1:5000/api/login", json=login_data)
print(f"Login response: {login_response.status_code}")
print(f"Login body: {login_response.text}")

if login_response.status_code == 200:
    token = login_response.json().get('token')  # Changed from 'access_token' to 'token'
    print(f"✓ Login successful, token: {token[:20]}...")
    
    # Test file upload
    print("\nTesting file upload...")
    test_content = """********************
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
********************"""
    
    with open("test.003", "w") as f:
        f.write(test_content)
    
    headers = {"Authorization": f"Bearer {token}"}
    with open("test.003", "rb") as f:
        files = {"files": ("test.003", f, "application/octet-stream")}
        upload_response = requests.post("http://127.0.0.1:5000/api/ej/load_logs", files=files, headers=headers)
    
    print(f"Upload response: {upload_response.status_code}")
    print(f"Upload body: {upload_response.text}")
    
    if upload_response.status_code == 200:
        print("✓ File upload and processing successful!")
        result = upload_response.json()
        print(f"  - Files processed: {result.get('files_processed')}")
        print(f"  - Transactions extracted: {result.get('transactions_extracted')}")
        print(f"  - Database saved: {result.get('database_saved')}")
    else:
        print("✗ Upload failed")
    
    # Clean up
    import os
    try:
        os.remove("test.003")
    except:
        pass
else:
    print("✗ Login failed")

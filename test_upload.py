#!/usr/bin/env python3
"""
Test script to test file upload with JWT authentication
"""

import requests
import json

BASE_URL = "http://localhost:5000/api"

def get_auth_token():
    """Get JWT token for testing"""
    login_data = {
        "email": "testuser2@example.com",
        "password": "TestPass123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        if response.status_code == 200:
            return response.json().get('token')
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login request failed: {e}")
        return None

def test_file_upload():
    """Test file upload with JWT authentication"""
    print("📤 Testing File Upload with JWT")
    print("=" * 50)
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication token")
        return
    
    print("✅ Authentication token obtained")
    
    # Prepare test file
    test_file_path = "test_file.003"
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'files': (test_file_path, f, 'application/octet-stream')}
            headers = {"Authorization": f"Bearer {token}"}
            
            print(f"📁 Uploading file: {test_file_path}")
            response = requests.post(f"{BASE_URL}/ej/load_logs", files=files, headers=headers)
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📊 Response Content: {response.text}")
            
            if response.status_code == 200:
                print("✅ File upload successful!")
                data = response.json()
                if 'transactions' in data:
                    print(f"   Transactions found: {len(data['transactions'])}")
                elif 'error' in data:
                    print(f"   Info: {data['error']}")
            elif response.status_code == 401:
                print("❌ Authentication failed - JWT token invalid or expired")
            elif response.status_code == 403:
                print("❌ Access forbidden - possibly trial expired")
            else:
                print(f"❌ Upload failed with status {response.status_code}")
                
    except FileNotFoundError:
        print(f"❌ Test file not found: {test_file_path}")
    except Exception as e:
        print(f"❌ Upload request failed: {e}")

if __name__ == "__main__":
    test_file_upload()

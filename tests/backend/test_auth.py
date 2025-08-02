#!/usr/bin/env python3
"""
Test script to create a test user and get a JWT token
"""

import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_auth():
    """Test authentication flow"""
    print("🔐 Testing Authentication Flow")
    print("=" * 50)    # Test data
    test_user = {
        "email": "testuser2@example.com",
        "username": "testuser2",
        "password": "TestPass123!",
        "repassword": "TestPass123!"
    }
    
    # Test registration
    print("1️⃣ Testing Registration...")
    try:
        response = requests.post(f"{BASE_URL}/register", json=test_user)
        if response.status_code == 201:
            print("✅ Registration successful!")
            print(f"   Response: {response.json()}")
        elif response.status_code == 400 and "already exists" in response.text:
            print("ℹ️ User already exists, continuing with login test...")
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Registration request failed: {e}")
    
    print()
    
    # Test login
    print("2️⃣ Testing Login...")
    try:
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"   Token received: {data.get('token', 'N/A')[:50]}...")
            print(f"   User: {data.get('user', {}).get('username', 'N/A')}")
            return data.get('token')
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login request failed: {e}")
        return None

def test_protected_endpoint(token):
    """Test JWT-protected endpoint"""
    if not token:
        print("❌ No token available for protected endpoint test")
        return
    
    print()
    print("3️⃣ Testing Protected Endpoint...")
    
    # Test the /ej/hello endpoint (which requires JWT)
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{BASE_URL}/ej/hello", headers=headers)
        if response.status_code == 200:
            print("✅ Protected endpoint access successful!")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Protected endpoint failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Protected endpoint request failed: {e}")

if __name__ == "__main__":
    token = test_auth()
    test_protected_endpoint(token)

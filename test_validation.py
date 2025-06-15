#!/usr/bin/env python3
"""
Test script to validate file extensions and JWT functionality
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.validators import validate_file_upload
from werkzeug.datastructures import FileStorage
from io import BytesIO

def test_file_extensions():
    """Test file extension validation"""
    print("🧪 Testing File Extension Validation")
    print("=" * 50)
    
    # Test cases: (filename, expected_valid)
    test_cases = [
        ("test.003", True),
        ("test.001", True),
        ("test.123", True),
        ("test.999", True),
        ("test.log", True),
        ("test.txt", True),
        ("test.ej", True),
        ("test.dat", True),
        ("test.pdf", False),
        ("test.exe", False),
        ("test.12", False),   # Only 2 digits
        ("test.1234", False), # 4 digits
        ("test.abc", False),  # Letters
        ("test.0a1", False),  # Mixed
    ]
    
    for filename, expected in test_cases:
        # Create a mock FileStorage object
        mock_file = FileStorage(
            stream=BytesIO(b"test content"),
            filename=filename,
            content_type="application/octet-stream"
        )
        
        result = validate_file_upload(mock_file)
        is_valid = result['valid']
        
        status = "✅ PASS" if is_valid == expected else "❌ FAIL"
        print(f"{status} {filename:<12} - Expected: {expected}, Got: {is_valid}")
        
        if not is_valid and 'error' in result:
            print(f"     Error: {result['error']}")
        
        print()

if __name__ == "__main__":
    test_file_extensions()

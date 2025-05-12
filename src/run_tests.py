#!/usr/bin/env python
"""
Test runner for NetCon_PyVue application.
This script discovers and runs all tests in the tests directory.
"""

import unittest
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def run_tests():
    """Discover and run all tests in the tests directory."""
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

if __name__ == '__main__':
    result = run_tests()
    
    # Exit with non-zero code if tests failed
    sys.exit(not result.wasSuccessful())

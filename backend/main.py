#!/usr/bin/env python3
"""
Main application entry point for NetCon backend.
This module serves as the entry point for running the Flask application.
"""

import os
import sys
from app import create_app

def main():
    """Main function to run the Flask application."""
    # Get configuration from environment or default to development
    config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Create the Flask application
    app = create_app(config_name)
    
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Get host from environment or default to localhost
    host = os.environ.get('HOST', '127.0.0.1')
    
    # Get debug mode from environment
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting NetCon backend server on {host}:{port}")
    print(f"Environment: {config_name}")
    print(f"Debug mode: {debug}")
    
    # Run the application
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()
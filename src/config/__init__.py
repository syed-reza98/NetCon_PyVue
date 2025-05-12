"""
Configuration package for the NetCon_PyVue application.
This package contains configuration settings and constants used throughout the application.
"""

import datetime

# Global application configuration
APP_CONFIG = {
    # Trial configuration
    "trial": {
        "start_date": datetime.datetime(2025, 5, 6),
        "duration_days": 15
    },
    
    # Currency denominations
    "currency": {
        "denominations": [100, 500, 1000]
    },
    
    # Logging configuration
    "logging": {
        "level": "INFO",
        "format": '%(asctime)s - %(levelname)s - %(message)s'
    }
}

def get_config(section=None, key=None):
    """
    Get configuration values from the APP_CONFIG dictionary.
    
    Args:
        section (str, optional): Configuration section name
        key (str, optional): Configuration key within the section
        
    Returns:
        The requested configuration value or section
        
    Raises:
        KeyError: If the section or key doesn't exist
    """
    if section is None:
        return APP_CONFIG
    
    if section not in APP_CONFIG:
        raise KeyError(f"Configuration section '{section}' not found")
    
    if key is None:
        return APP_CONFIG[section]
    
    if key not in APP_CONFIG[section]:
        raise KeyError(f"Configuration key '{key}' not found in section '{section}'")
    
    return APP_CONFIG[section][key]

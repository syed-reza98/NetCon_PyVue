"""
Validation utilities for file uploads and data validation.
"""

import os
import re
from typing import Dict, Any, Optional
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage


def validate_file_upload(file: FileStorage) -> Dict[str, Any]:
    """
    Validate uploaded file for security and format requirements.
    
    Args:
        file: Uploaded file object
        
    Returns:
        Dictionary with validation result
    """
    if not file or not file.filename:
        return {'valid': False, 'error': 'No file provided'}
    
    # Check file extension
    # Allow file extensions like: .001, .002, .012, .123 {Any 3 digits after the dot}
    
    allowed_extensions = {'.log', '.txt', '.ej', '.dat'}
    
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    # Allow extensions like .001, .002, .123 (any 3 digits after the dot)
    digit_ext_pattern = r'^\.\d{3}$'
    if file_ext not in allowed_extensions and not re.match(digit_ext_pattern, file_ext):
        allowed_types = ", ".join(list(allowed_extensions) + ['.### (3 digits)'])
        return {
            'valid': False, 
            'error': f'File type {file_ext} not allowed. Allowed types: {allowed_types}'
        }
    
    # Check file size (limit to 10MB per file)
    max_size = 10 * 1024 * 1024  # 10MB
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset position
    
    if file_size > max_size:
        return {
            'valid': False,
            'error': f'File size {file_size // (1024*1024)}MB exceeds limit of {max_size // (1024*1024)}MB'
        }
    
    # Check filename for security
    secure_name = secure_filename(file.filename)
    if not secure_name or secure_name != file.filename:
        return {
            'valid': False,
            'error': 'Filename contains invalid characters'
        }
    
    return {'valid': True, 'error': None}


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return 'unknown_file'
    
    # Use werkzeug's secure_filename
    sanitized = secure_filename(filename)
    
    # Ensure we have a filename
    if not sanitized:
        sanitized = 'sanitized_file'
    
    return sanitized


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        Dictionary with validation result and details
    """
    if not password:
        return {'valid': False, 'error': 'Password is required', 'strength': 0}
    
    errors = []
    strength = 0
    
    # Length check
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    else:
        strength += 1
    
    # Character type checks
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter')
    else:
        strength += 1
    
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter')
    else:
        strength += 1
    
    if not re.search(r'\d', password):
        errors.append('Password must contain at least one number')
    else:
        strength += 1
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append('Password must contain at least one special character')
    else:
        strength += 1
    
    # Common password check
    common_passwords = {'password', '123456', 'password123', 'admin', 'qwerty'}
    if password.lower() in common_passwords:
        errors.append('Password is too common')
        strength = max(0, strength - 2)
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'strength': strength,
        'strength_text': _get_strength_text(strength)
    }


def _get_strength_text(strength: int) -> str:
    """Get password strength text description"""
    if strength <= 1:
        return 'Very Weak'
    elif strength == 2:
        return 'Weak'
    elif strength == 3:
        return 'Medium'
    elif strength == 4:
        return 'Strong'
    else:
        return 'Very Strong'


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format (simple validation).
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid phone format
    """
    if not phone:
        return False
    
    # Remove common separators
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Check length and format
    if len(cleaned) < 10 or len(cleaned) > 15:
        return False
    
    # Should start with + or digit
    return cleaned[0] in '+0123456789'


def sanitize_input(input_str: str, max_length: int = 255) -> str:
    """
    Sanitize user input by removing dangerous characters.
    
    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not input_str:
        return ''
    
    # Remove null bytes and control characters
    sanitized = input_str.replace('\x00', '').replace('\r', '').replace('\n', ' ')
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Strip whitespace
    return sanitized.strip()


def validate_json_data(data: Any, required_fields: Optional[list] = None) -> Dict[str, Any]:
    """
    Validate JSON data structure.
    
    Args:
        data: Data to validate
        required_fields: List of required field names
        
    Returns:
        Dictionary with validation result
    """
    if not isinstance(data, dict):
        return {'valid': False, 'error': 'Data must be a JSON object'}
    
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return {
                'valid': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }
    
    return {'valid': True, 'error': None}

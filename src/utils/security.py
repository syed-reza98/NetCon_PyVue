"""
Security utilities for rate limiting, logging, and security monitoring.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from flask import request, current_app
import hashlib
import hmac

# Security event logger
security_logger = logging.getLogger('security')

# In-memory storage for rate limiting (in production, use Redis)
_rate_limit_storage = defaultdict(deque)
_failed_attempts = defaultdict(int)
_security_events = deque(maxlen=1000)


def check_rate_limit(identifier: str, limit: int, window_seconds: int = 60) -> bool:
    """
    Check if request is within rate limit.
    
    Args:
        identifier: Unique identifier (IP, user ID, etc.)
        limit: Maximum number of requests allowed
        window_seconds: Time window in seconds
        
    Returns:
        True if within limit, False otherwise
    """
    now = datetime.now(timezone.utc)
    window_start = now.timestamp() - window_seconds
    
    # Clean old entries
    request_times = _rate_limit_storage[identifier]
    while request_times and request_times[0] < window_start:
        request_times.popleft()
    
    # Check if limit exceeded
    if len(request_times) >= limit:
        log_security_event('rate_limit_exceeded', {
            'identifier': identifier,
            'limit': limit,
            'window_seconds': window_seconds,
            'current_requests': len(request_times)
        })
        return False
    
    # Add current request
    request_times.append(now.timestamp())
    return True


def log_security_event(event_type: str, details: Dict[str, Any], 
                      level: str = 'WARNING') -> None:
    """
    Log security-related events.
    
    Args:
        event_type: Type of security event
        details: Event details
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    event_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event_type': event_type,
        'details': details,
        'request_info': _get_request_info() if request else None
    }
    
    # Store in memory (in production, use proper storage)
    _security_events.append(event_data)
    
    # Log to security logger
    log_message = f"Security Event: {event_type} - {json.dumps(details)}"
    getattr(security_logger, level.lower())(log_message)


def _get_request_info() -> Dict[str, Any]:
    """Get current request information for security logging"""
    try:
        return {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'method': request.method,
            'path': request.path,
            'referrer': request.headers.get('Referer', ''),
            'content_type': request.headers.get('Content-Type', '')
        }
    except Exception:
        return {}


def track_failed_login(identifier: str) -> int:
    """
    Track failed login attempts.
    
    Args:
        identifier: User identifier (email, username, IP)
        
    Returns:
        Number of failed attempts
    """
    _failed_attempts[identifier] += 1
    
    log_security_event('failed_login_attempt', {
        'identifier': identifier,
        'attempt_count': _failed_attempts[identifier]
    })
    
    return _failed_attempts[identifier]


def is_account_locked(identifier: str, max_attempts: int = 5) -> bool:
    """
    Check if account is locked due to failed attempts.
    
    Args:
        identifier: User identifier
        max_attempts: Maximum allowed failed attempts
        
    Returns:
        True if account is locked
    """
    return _failed_attempts.get(identifier, 0) >= max_attempts


def reset_failed_attempts(identifier: str) -> None:
    """Reset failed login attempts for identifier"""
    if identifier in _failed_attempts:
        del _failed_attempts[identifier]
        
        log_security_event('login_attempts_reset', {
            'identifier': identifier
        }, level='INFO')


def generate_csrf_token(secret_key: str, user_id: str) -> str:
    """
    Generate CSRF token.
    
    Args:
        secret_key: Application secret key
        user_id: User identifier
        
    Returns:
        CSRF token
    """
    timestamp = str(int(datetime.now(timezone.utc).timestamp()))
    message = f"{user_id}:{timestamp}"
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{message}:{signature}"


def validate_csrf_token(token: str, secret_key: str, user_id: str, 
                       max_age_seconds: int = 3600) -> bool:
    """
    Validate CSRF token.
    
    Args:
        token: CSRF token to validate
        secret_key: Application secret key
        user_id: Expected user identifier
        max_age_seconds: Maximum token age in seconds
        
    Returns:
        True if token is valid
    """
    try:
        parts = token.split(':')
        if len(parts) != 3:
            return False
        
        token_user_id, timestamp_str, signature = parts
        
        # Check user ID match
        if token_user_id != user_id:
            return False
        
        # Check timestamp
        timestamp = int(timestamp_str)
        now = int(datetime.now(timezone.utc).timestamp())
        if now - timestamp > max_age_seconds:
            return False
        
        # Verify signature
        message = f"{token_user_id}:{timestamp_str}"
        expected_signature = hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception as e:
        log_security_event('csrf_validation_error', {
            'error': str(e),
            'token_preview': token[:20] + '...' if len(token) > 20 else token
        })
        return False


def sanitize_sql_input(input_str: str) -> str:
    """
    Basic SQL injection prevention (use parameterized queries instead).
    
    Args:
        input_str: Input string
        
    Returns:
        Sanitized string
    """
    if not input_str:
        return ''
    
    # Remove common SQL injection patterns
    dangerous_patterns = [
        ';', '--', '/*', '*/', 'xp_', 'sp_', 'EXEC', 'EXECUTE',
        'DROP', 'DELETE', 'INSERT', 'UPDATE', 'UNION', 'SELECT'
    ]
    
    sanitized = input_str
    for pattern in dangerous_patterns:
        sanitized = sanitized.replace(pattern, '')
    
    return sanitized


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """
    Hash password with salt.
    
    Args:
        password: Password to hash
        salt: Optional salt (generates new if not provided)
        
    Returns:
        Tuple of (hashed_password, salt)
    """
    if salt is None:
        salt = hashlib.sha256(str(datetime.now(timezone.utc).timestamp()).encode()).hexdigest()[:16]
    

    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return hashed.hex(), salt


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        password: Plain text password
        hashed_password: Stored hash
        salt: Salt used for hashing
        
    Returns:
        True if password matches
    """
    try:
        test_hash, _ = hash_password(password, salt)
        return hmac.compare_digest(test_hash, hashed_password)
    except Exception:
        return False


def get_security_events(limit: int = 100) -> list:
    """
    Get recent security events.
    
    Args:
        limit: Maximum number of events to return
        
    Returns:
        List of security events
    """
    return list(_security_events)[-limit:]


def detect_suspicious_activity(user_id: str, activity_type: str) -> bool:
    """
    Detect suspicious activity patterns.
    
    Args:
        user_id: User identifier
        activity_type: Type of activity
        
    Returns:
        True if activity seems suspicious
    """
    # Simple heuristic - check for rapid successive activities
    now = datetime.now(timezone.utc).timestamp()
    recent_events = [
        event for event in _security_events
        if (event.get('details', {}).get('user_id') == user_id and
            event.get('details', {}).get('activity_type') == activity_type and
            (now - datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')).timestamp()) < 60)
    ]
    
    if len(recent_events) > 10:  # More than 10 activities in 1 minute
        log_security_event('suspicious_activity_detected', {
            'user_id': user_id,
            'activity_type': activity_type,
            'event_count': len(recent_events),
            'time_window': '60 seconds'
        })
        return True
    
    return False


def mask_sensitive_data(data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging.
    
    Args:
        data: Data to mask
        mask_char: Character to use for masking
        visible_chars: Number of characters to keep visible at the end
        
    Returns:
        Masked string
    """
    if not data or len(data) <= visible_chars:
        return mask_char * len(data) if data else ''
    
    return mask_char * (len(data) - visible_chars) + data[-visible_chars:]

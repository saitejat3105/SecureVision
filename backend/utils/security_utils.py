#security_utils.py
import hashlib
import secrets
import hmac
import base64
from datetime import datetime, timedelta

def generate_token(length=32):
    """Generate secure random token"""
    return secrets.token_urlsafe(length)

def hash_data(data, salt=None):
    """Hash data with optional salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    hashed = hashlib.sha256((data + salt).encode()).hexdigest()
    return f"{salt}:{hashed}"

def verify_hash(stored_hash, data):
    """Verify data against stored hash"""
    try:
        salt, hashed = stored_hash.split(':')
        expected = hashlib.sha256((data + salt).encode()).hexdigest()
        return hmac.compare_digest(hashed, expected)
    except:
        return False

def generate_api_key():
    """Generate API key"""
    return f"sv_{secrets.token_urlsafe(32)}"

def validate_api_key(key):
    """Validate API key format"""
    return key.startswith('sv_') and len(key) > 35

def create_session_token(user_id, expiry_hours=24):
    """Create session token"""
    expiry = datetime.now() + timedelta(hours=expiry_hours)
    data = f"{user_id}:{expiry.timestamp()}"
    signature = hashlib.sha256(data.encode()).hexdigest()[:16]
    token = base64.urlsafe_b64encode(f"{data}:{signature}".encode()).decode()
    return token

def validate_session_token(token):
    """Validate session token"""
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        user_id, expiry_ts, signature = decoded.rsplit(':', 2)
        
        # Check expiry
        if float(expiry_ts) < datetime.now().timestamp():
            return None
        
        # Verify signature
        data = f"{user_id}:{expiry_ts}"
        expected_sig = hashlib.sha256(data.encode()).hexdigest()[:16]
        
        if hmac.compare_digest(signature, expected_sig):
            return user_id
        return None
    except:
        return None

def sanitize_filename(filename):
    """Sanitize filename to prevent path traversal"""
    import re
    # Remove path separators and special characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    return sanitized if sanitized else 'unnamed'
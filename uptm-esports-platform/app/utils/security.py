import os
import hashlib
import json
from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from config import Config

def _get_aes_key() -> bytes:
    """Retrieve or derive a 32-byte key for AES-256."""
    raw_key = Config.ENCRYPTION_KEY
    try:
        key_bytes = bytes.fromhex(raw_key)
        if len(key_bytes) == 32:
            return key_bytes
    except Exception:
        pass
    # Fallback to SHA-256 digest of key string to guarantee exactly 32 bytes
    return hashlib.sha256(raw_key.encode('utf-8')).digest()

def encrypt_pii(plaintext: str | None) -> str | None:
    """Encrypt sensitive PII using AES-256-GCM."""
    if not plaintext:
        return None
    try:
        key = _get_aes_key()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        # Store as nonce:ciphertext in hex
        return f"{nonce.hex()}:{ciphertext.hex()}"
    except Exception:
        return plaintext

def decrypt_pii(stored_val: str | None) -> str | None:
    """Decrypt sensitive PII encrypted with AES-256-GCM."""
    if not stored_val:
        return None
    try:
        if ':' not in stored_val:
            return stored_val
        nonce_hex, ciphertext_hex = stored_val.split(':', 1)
        nonce = bytes.fromhex(nonce_hex)
        ciphertext = bytes.fromhex(ciphertext_hex)
        key = _get_aes_key()
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted.decode('utf-8')
    except Exception:
        return stored_val

def is_allowed_uptm_email(email: str) -> bool:
    """Verify that email belongs to allowed UPTM domains."""
    if not email or '@' not in email:
        return False
    domain = email.lower().split('@')[-1].strip()
    return domain in Config.ALLOWED_EMAIL_DOMAINS

def compute_audit_hash(actor_id: str, action: str, target_type: str, target_id: str, prev_hash: str, timestamp: str) -> str:
    """Generate SHA-256 hash chaining for immutable audit logs."""
    record_str = f"{actor_id}:{action}:{target_type}:{target_id}:{prev_hash}:{timestamp}"
    return hashlib.sha256(record_str.encode('utf-8')).hexdigest()

def role_required(*allowed_roles):
    """Decorator to require specific user roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please sign in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            if current_user.role not in allowed_roles:
                flash('Access denied: You do not have permission to view this resource.', 'danger')
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required('ADMIN')(f)

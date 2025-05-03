import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.core.config import settings

def generate_key(password: str, salt: bytes = None) -> bytes:
    """Generate encryption key from password."""
    if salt is None:
        salt = b'email_assistant_salt'  # Default salt, should be stored securely in production
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def encrypt_data(data: str, key: bytes) -> str:
    """Encrypt sensitive data."""
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str, key: bytes) -> str:
    """Decrypt sensitive data."""
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()

# For storing email credentials securely
def secure_credentials():
    """Utility to securely store email credentials."""
    key = generate_key(settings.PROJECT_NAME)
    encrypted_password = encrypt_data(settings.EMAIL_PASSWORD, key)
    return {
        "host": settings.EMAIL_HOST,
        "user": settings.EMAIL_USER,
        "password": encrypted_password,
        "key": key
    } 
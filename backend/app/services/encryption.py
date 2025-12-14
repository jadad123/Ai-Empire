from cryptography.fernet import Fernet
from app.config import settings
import base64
import hashlib


class EncryptionService:
    def __init__(self):
        key = settings.encryption_key
        if not key:
            # Generate a new key if none provided
            key = Fernet.generate_key().decode()
        else:
            # If key is not valid Fernet format, create one from it
            try:
                # Try to use the key directly
                if isinstance(key, str):
                    key = key.encode()
                Fernet(key)  # Test if valid
            except Exception:
                # Key is not valid Fernet format, derive one from it
                if isinstance(key, str):
                    key = key.encode()
                # Create a valid 32-byte key from the provided key using SHA256
                derived_key = hashlib.sha256(key).digest()
                key = base64.urlsafe_b64encode(derived_key)
        
        self.cipher = Fernet(key if isinstance(key, bytes) else key.encode())
    
    def encrypt(self, data: str) -> str:
        if not data:
            return ""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        if not encrypted_data:
            return ""
        return self.cipher.decrypt(encrypted_data.encode()).decode()


encryption_service = EncryptionService()

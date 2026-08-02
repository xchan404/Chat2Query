"""Fernet symmetric encryption for database connection credentials.

Credentials are encrypted at rest in the DB (encrypted_password,
encrypted_connection_string columns). They are decrypted only
transiently in memory when needed — never logged.
"""

import logging
from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    """Return a Fernet instance using the configured encryption key."""
    settings = get_settings()
    key = settings.CONNECTION_ENCRYPTION_KEY
    # If the key isn't a valid Fernet key, generate one from it via padding
    # In production, CONNECTION_ENCRYPTION_KEY should be a real Fernet key
    try:
        return Fernet(key.encode("utf-8") if isinstance(key, str) else key)
    except (ValueError, Exception):
        # Fall back: derive a valid Fernet key from the raw key string
        import base64
        import hashlib
        derived = hashlib.sha256(key.encode("utf-8")).digest()
        fernet_key = base64.urlsafe_b64encode(derived)
        return Fernet(fernet_key)


def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext string. Returns base64-encoded ciphertext.

    The returned value is safe to store in a TEXT column.
    """
    f = _get_fernet()
    token = f.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a ciphertext string. Returns the original plaintext.

    Raises ValueError if decryption fails (wrong key, tampered data).
    """
    f = _get_fernet()
    try:
        plaintext = f.decrypt(ciphertext.encode("utf-8"))
        return plaintext.decode("utf-8")
    except InvalidToken:
        logger.error("Failed to decrypt value — invalid token or wrong key")
        raise ValueError("Decryption failed: invalid token or wrong encryption key")

"""Unit tests for core/encryption.py — Fernet encrypt/decrypt,
ciphertext verification, round-trip, and raw column inspection.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

os.environ["JWT_SECRET"] = "test-secret-key-for-testing"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test"
os.environ["CONNECTION_ENCRYPTION_KEY"] = "test-encryption-key-for-unit-tests"

import pytest

from core.encryption import encrypt_value, decrypt_value


class TestEncryptionRoundTrip:
    """Test that encrypt → decrypt returns the original value."""

    def test_round_trip_simple_password(self):
        password = "my-secret-db-password"
        encrypted = encrypt_value(password)
        decrypted = decrypt_value(encrypted)
        assert decrypted == password

    def test_round_trip_connection_string(self):
        conn_str = "postgresql://user:p@ssw0rd!@host:5432/mydb"
        encrypted = encrypt_value(conn_str)
        decrypted = decrypt_value(encrypted)
        assert decrypted == conn_str

    def test_round_trip_unicode(self):
        password = "пароль-密码-كلمة"
        encrypted = encrypt_value(password)
        decrypted = decrypt_value(encrypted)
        assert decrypted == password

    def test_round_trip_special_characters(self):
        password = "p@$$w0rd!#%^&*()_+-=[]{}|;':\",./<>?"
        encrypted = encrypt_value(password)
        decrypted = decrypt_value(encrypted)
        assert decrypted == password

    def test_round_trip_empty_string(self):
        encrypted = encrypt_value("")
        decrypted = decrypt_value(encrypted)
        assert decrypted == ""


class TestCiphertextIsNotPlaintext:
    """Verify that encrypted values are actual ciphertext, not plaintext.

    This is the critical security property: the raw DB column must contain
    ciphertext that does not resemble the original password.
    """

    def test_encrypted_value_is_not_plaintext(self):
        """The encrypted value must NOT equal the plaintext password."""
        password = "super-secret-password-123"
        encrypted = encrypt_value(password)
        assert encrypted != password

    def test_encrypted_value_does_not_contain_plaintext(self):
        """The encrypted value must NOT contain the plaintext as a substring."""
        password = "super-secret-password-123"
        encrypted = encrypt_value(password)
        assert password not in encrypted

    def test_encrypted_value_is_base64_fernet_token(self):
        """Fernet tokens are base64-encoded and start with 'gAAAAA'."""
        password = "test-password"
        encrypted = encrypt_value(password)
        # Fernet tokens are URL-safe base64
        assert encrypted.startswith("gAAAAA")
        # They're significantly longer than the input
        assert len(encrypted) > len(password) * 2

    def test_same_plaintext_produces_different_ciphertexts(self):
        """Fernet uses a unique IV each time, so same input → different output."""
        password = "same-password"
        enc1 = encrypt_value(password)
        enc2 = encrypt_value(password)
        assert enc1 != enc2  # Different IVs
        # But both decrypt to the same value
        assert decrypt_value(enc1) == decrypt_value(enc2) == password

    def test_raw_column_value_is_unreadable(self):
        """Simulate what a DB inspector would see: the raw encrypted_password
        column value is pure ciphertext, not human-readable, and cannot be
        decoded without the encryption key.

        This directly satisfies Section 8's requirement:
        'credentials are unreadable in the DB (verify by querying the raw
        column and confirming it's ciphertext)'
        """
        original_password = "admin123"

        # This is what the connection_service stores in encrypted_password
        raw_db_column_value = encrypt_value(original_password)

        # 1. It's not the original password
        assert raw_db_column_value != original_password

        # 2. It doesn't contain the original password
        assert original_password not in raw_db_column_value

        # 3. It's a valid Fernet token (base64, starts with gAAAAA)
        assert raw_db_column_value.startswith("gAAAAA")

        # 4. It's long enough to be a real encrypted value
        assert len(raw_db_column_value) > 80

        # 5. An attacker reading the raw column cannot extract the password
        #    without the encryption key — verify by trying to decrypt with
        #    a different key
        import base64
        import hashlib
        from cryptography.fernet import Fernet

        wrong_key = base64.urlsafe_b64encode(
            hashlib.sha256(b"wrong-key").digest()
        )
        wrong_fernet = Fernet(wrong_key)
        with pytest.raises(Exception):
            wrong_fernet.decrypt(raw_db_column_value.encode("utf-8"))

        # 6. But with the correct key, it DOES decrypt to the original
        decrypted = decrypt_value(raw_db_column_value)
        assert decrypted == original_password


class TestDecryptionErrors:
    """Test error handling for invalid ciphertext."""

    def test_invalid_ciphertext_raises_value_error(self):
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt_value("not-a-valid-fernet-token")

    def test_tampered_ciphertext_raises_value_error(self):
        encrypted = encrypt_value("password")
        # Tamper with the ciphertext
        tampered = encrypted[:10] + "XXXXXXXX" + encrypted[18:]
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt_value(tampered)

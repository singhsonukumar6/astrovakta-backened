"""
AES encryption for AI provider API keys at rest.
Uses Fernet (AES-128-CBC) from the cryptography library.
"""
import os
import base64
import secrets
from pathlib import Path

_KEY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".encryption_key")


def _load_or_create_key() -> bytes:
    """Load encryption key from file or env, or generate a new one."""
    env_key = os.environ.get("ENCRYPTION_KEY")
    if env_key:
        return env_key.encode() if isinstance(env_key, str) else env_key

    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE, "rb") as f:
            return f.read().strip()

    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    with open(_KEY_FILE, "wb") as f:
        f.write(key)
    os.chmod(_KEY_FILE, 0o600)
    return key


_fernet = None


def _get_fernet():
    global _fernet
    if _fernet is None:
        from cryptography.fernet import Fernet
        _fernet = Fernet(_load_or_create_key())
    return _fernet


def encrypt_api_key(plain_text: str) -> str:
    """Encrypt an API key string. Returns URL-safe base64 encoded ciphertext."""
    if not plain_text:
        return ""
    f = _get_fernet()
    encrypted = f.encrypt(plain_text.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_api_key(cipher_text: str) -> str:
    """Decrypt an encrypted API key back to plaintext."""
    if not cipher_text:
        return ""
    f = _get_fernet()
    decrypted = f.decrypt(cipher_text.encode("utf-8"))
    return decrypted.decode("utf-8")


def mask_api_key(plain_key: str) -> str:
    """Return a masked version of an API key for display: sk-ab...xyz"""
    if not plain_key or len(plain_key) < 8:
        return "****"
    return plain_key[:6] + "..." + plain_key[-4:]

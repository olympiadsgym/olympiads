import base64
import hashlib
import hmac
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


def _load_key() -> bytes:
    raw = getattr(settings, "FIELD_ENCRYPTION_KEY", None)
    if not raw:
        raise RuntimeError(
            "FIELD_ENCRYPTION_KEY is not set. Add it to your .env and settings.py."
        )
    try:
        key = base64.urlsafe_b64decode(raw + "==")
    except Exception as exc:
        raise RuntimeError(f"FIELD_ENCRYPTION_KEY is not valid base64url: {exc}") from exc
    if len(key) != 32:
        raise RuntimeError(
            f"FIELD_ENCRYPTION_KEY must decode to exactly 32 bytes, got {len(key)}."
        )
    return key


def encrypt(plaintext: str) -> str:
    if plaintext is None:
        return ""
    key = _load_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.urlsafe_b64encode(nonce + ct).decode()


def decrypt(token: str) -> str:
    if not token:
        return ""
    key = _load_key()
    try:
        raw = base64.urlsafe_b64decode(token + "==")
    except Exception as exc:
        raise ValueError("Encrypted field is not valid base64url.") from exc
    if len(raw) < 28:
        raise ValueError("Encrypted field is too short.")
    nonce, ct = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(nonce, ct, None).decode()
    except Exception as exc:
        raise ValueError("Decryption failed — data may be tampered.") from exc


def make_lookup_hash(value: str) -> str:
    if not value:
        return ""
    key = _load_key()
    return hmac.new(key, value.lower().encode(), hashlib.sha256).hexdigest()


def mask_email(email: str) -> str:
    if not email or '@' not in email:
        return email
    local, domain = email.split('@', 1)
    if len(local) <= 1:
        masked_local = '*'
    else:
        masked_local = local[0] + '***'
    return f"{masked_local}@{domain}"

class EncryptedFieldDescriptor:
    def __init__(self, field_name: str):
        self.field_name = field_name

    def __set_name__(self, owner, name):
        self.attr_name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        raw = getattr(obj, self.field_name)
        if not raw:
            return raw
        if len(raw) < 40:
            return raw
        try:
            return decrypt(raw)
        except ValueError:
            return raw

    def __set__(self, obj, value):
        if value is None or value == "":
            setattr(obj, self.field_name, value)
        else:
            setattr(obj, self.field_name, encrypt(value))
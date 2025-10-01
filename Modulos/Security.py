import os
import binascii
import hashlib
import hmac


DEFAULT_ALG = 'pbkdf2_sha256'
DEFAULT_ITERS = 260_000


def _pbkdf2_sha256(password: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)


def hash_password(password: str, iterations: int = DEFAULT_ITERS) -> str:
    """Genera un hash tipo: pbkdf2_sha256$iters$salt$hashhex"""
    salt = os.urandom(16)
    dk = _pbkdf2_sha256(password, salt, iterations)
    return f"{DEFAULT_ALG}${iterations}${binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        alg, iters_str, salt_hex, hash_hex = stored.split('$', 3)
        if alg != DEFAULT_ALG:
            return False
        iterations = int(iters_str)
        salt = binascii.unhexlify(salt_hex)
        expected = binascii.unhexlify(hash_hex)
        dk = _pbkdf2_sha256(password, salt, iterations)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


def is_hashed(stored: str) -> bool:
    return isinstance(stored, str) and stored.startswith(f"{DEFAULT_ALG}$") and stored.count('$') == 3


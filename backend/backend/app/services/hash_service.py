"""SHA-256 evidence integrity hashing (spec section 15)."""

import hashlib


def sha256_hex(data: bytes) -> str:
    """Digital fingerprint of the original uploaded bytes, unmodified."""
    return hashlib.sha256(data).hexdigest()

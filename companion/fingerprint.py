"""Content fingerprints: equal after normalisation means the same text for the companion's purposes."""
import hashlib
import re


def normalize(text: str) -> str:
    """Case-fold and collapse whitespace. Nothing semantic: two lines that differ in a number stay different."""
    return re.sub(r"\s+", " ", text.strip().lower())


def fingerprint(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(normalize(p).encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()

"""Content fingerprints over the exact text.

Until 2026-09-27 the fingerprint (the cache key) and dedup case-folded and collapsed whitespace first, on the
claim that this was "nothing semantic". It was semantic: a case-sensitive value (an id, a hash, "aB12" vs
"Ab12") was served from the cache for a log that said something else, a log in which the tool found nothing
got a cached deterministic answer, and dedup dropped a conflicting line. The sovereign-veritas check PASSes a
CACHED answer of deterministic origin, so each of these could be ALLOWed. Found by cache_attack.py on the S25;
reproduced by experiments/C007_cache_collision/repro.py. The key is now the exact text; normalize() is kept
for display and analysis only and is used by nothing that decides an answer.
"""
import hashlib
import re


def normalize(text: str) -> str:
    """Case-fold and collapse whitespace. For display and analysis only: NOT safe as a key (see the module doc)."""
    return re.sub(r"\s+", " ", text.strip().lower())


def fingerprint(*parts: str) -> str:
    """SHA-256 over the exact parts, each length-prefixed so that part boundaries cannot be shifted."""
    h = hashlib.sha256()
    for p in parts:
        b = p.encode("utf-8")
        h.update(len(b).to_bytes(8, "big"))
        h.update(b)
    return h.hexdigest()

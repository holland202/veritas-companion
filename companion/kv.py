"""A deterministic key = value reader for real logs (C002). One pair per line: the first `key = value`."""
import re

KV = re.compile(r"(?:^|\|\s*|:\s+|\s)([A-Za-z_][A-Za-z0-9_.\- ]{0,40}?)\s*=\s*([^\s,|;()]+)")


def norm_key(k):
    return re.sub(r"\s+", " ", k.strip().lower())


def parse_kv(line):
    m = KV.search(line)
    if not m:
        return None
    key, val = norm_key(m.group(1)), m.group(2).strip()
    if not key or not val or len(key) < 2:
        return None
    return key, val

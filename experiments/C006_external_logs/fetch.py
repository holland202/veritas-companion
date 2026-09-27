#!/usr/bin/env python3
"""Fetch the Loghub HDFS 2k sample and refuse to continue unless every file matches the hash frozen in
PREREG.md. Loghub: https://github.com/logpai/loghub (free for research use; cite the repository).
The files are not committed to this repository.   python experiments/C006_external_logs/fetch.py"""
import hashlib, os, sys, urllib.request

BASE = "https://raw.githubusercontent.com/logpai/loghub/master/HDFS/"
FROZEN = {  # recorded 2026-09-27 at the first download, before any tool or question touched the data
    "HDFS_2k.log": "7c967000980c086ed55fa6544ba4f05fe66d44622795e890c68caf8bbb635035",
    "HDFS_2k.log_structured.csv": "729df59774e3dde934044028546d2a55d5e3d4370b9d12fcebbe4c087b2bf7b4",
    "HDFS_2k.log_templates.csv": "a07307511f67c9dc1f41ae730ae60dcce8360f2c72742f0b8a3a9cf1a403d1db",
}
DEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "loghub_hdfs")


def main():
    os.makedirs(DEST, exist_ok=True)
    bad = 0
    for name, want in FROZEN.items():
        path = os.path.join(DEST, name)
        if not os.path.exists(path):
            try:
                urllib.request.urlretrieve(BASE + name, path)
            except OSError as exc:
                print(f"COULD NOT RUN: {name}: {exc}")
                sys.exit(2)
        got = hashlib.sha256(open(path, "rb").read()).hexdigest()
        ok = got == want
        bad += not ok
        print(f"{'OK  ' if ok else 'BAD '} {name}  {got}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

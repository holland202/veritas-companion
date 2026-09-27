#!/usr/bin/env python3
"""Fetch the Loghub HPC 2k sample and refuse to continue unless every file matches the hash frozen in
PREREG.md. Loghub: https://github.com/logpai/loghub (free for research use; cite the repository).
The files are not committed to this repository.   python experiments/C006b_hpc/fetch.py"""
import hashlib, os, sys, urllib.request

BASE = "https://raw.githubusercontent.com/logpai/loghub/master/HPC/"
FROZEN = {  # recorded 2026-09-27 at the first download, before any tool or question touched the data
    "HPC_2k.log": "826e5957b461e65780a8bda5c186c2fcf90fd6c1863721ef9c1ccfa9ada86f88",
    "HPC_2k.log_structured.csv": "0787df9cfab7e9495669548315ea8a9a51b02029c0dcfa28944707ad755a8c86",
    "HPC_2k.log_templates.csv": "c6b56ad5537b91a95e88a5953f7abfd7e8b36121673a4123eff7bf3e700d6775",
}
DEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "loghub_hpc")


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

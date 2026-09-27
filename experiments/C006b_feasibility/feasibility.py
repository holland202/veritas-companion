#!/usr/bin/env python3
"""C006b feasibility gate, run BEFORE any registration (C006 failed for lack of this; see ../C006_external_logs/RESULTS.md).

Reads only structure from Loghub 2k structured CSVs: how often a key recurs, and how guessable each
question template is without order. No log content, no question text, no truth values are printed.
  python experiments/C006b_feasibility/feasibility.py DIR   (DIR holds <System>_2k.log_structured.csv)
A template passes if >= 20 keys have >= 3 lines, a majority guess scores <= 0.5, and a shuffled key
keeps the same answer <= 0.5 of the time (so P3's registered 0.25 drop is reachable at all).
"""
import csv, os, random, sys
from collections import Counter, defaultdict
KEYS = {"OpenSSH": "Pid", "HPC": "Node", "Hadoop": "Process", "Android": "Pid", "Zookeeper": "Node"}
d = sys.argv[1]
for name, key in KEYS.items():
    rows = list(csv.DictReader(open(os.path.join(d, f"{name}_2k.log_structured.csv"), encoding="utf-8", errors="replace")))
    g = defaultdict(list)
    for r in rows:
        g[r[key]].append(r)
    ks = [sorted(v, key=lambda r: int(r["LineId"])) for v in g.values() if len(v) >= 3]
    print(f"{name}: key {key}, {len(g)} keys, {len(ks)} with >= 3 lines")
    if len(ks) < 20:
        print("  FAIL fewer than 20 usable keys"); continue
    rnd = random.Random(6)
    for tname, f in (("last event", lambda v: v[-1]["EventId"]), ("first event", lambda v: v[0]["EventId"]),
                     ("first component", lambda v: v[0].get("Component", ""))):
        maj = Counter(f(v) for v in ks).most_common(1)[0][1] / len(ks)
        kept = 0
        for v in ks:
            w = v[:]; rnd.shuffle(w); kept += f(w) == f(v)
        kept /= len(ks)
        ok = maj <= 0.5 and kept <= 0.5
        print(f"  {tname:<16} majority guess {maj:.3f}  shuffled same {kept:.3f}  {'PASS' if ok else 'FAIL'}")

#!/usr/bin/env python3
"""Run C003's deterministic part over seeds 1-20 and score D1-D3 (registered in PREREG.md)."""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
rows = []
for s in range(1, 21):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as fh:
        path = fh.name
    subprocess.run([sys.executable, os.path.join(HERE, "run.py"), "--seed", str(s), "--json", path], check=True,
                   stdout=subprocess.DEVNULL)
    rows.append(json.load(open(path))); os.unlink(path)
Q = sum(r["questions"] for r in rows)
ok = sum(r["routing_ok"] for r in rows); fs = sum(r["false_supported"] for r in rows)
nw = sum(r["naive_wrong_on_L0"] for r in rows); l0 = sum(r["L0_questions"] for r in rows)
kd = sum(r["evidence_kept_dedup"] for r in rows); kr = sum(r["evidence_kept_random"] for r in rows)
print(f"C003 deterministic, seeds 1-20: {Q} questions")
v = {"D1": (ok / Q >= 0.99 and fs == 0, f"routing {ok}/{Q} = {ok / Q:.4f}; false SUPPORTED on conflicts {fs}"),
     "D2": (nw / l0 >= 0.30, f"naive null wrong on {nw}/{l0} L0 questions = {nw / l0:.4f}"),
     "D3": (kd == Q and kr < kd, f"evidence kept: dedup {kd}/{Q}, random {kr}/{Q}")}
for k, (g, d) in v.items():
    print(f"{'HELD  ' if g else 'FAILED'} {k}  {d}")
print(f"VERDICT  {sum(g for g, _ in v.values())} of 3 held")

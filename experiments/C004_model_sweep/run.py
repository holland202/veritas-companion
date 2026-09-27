#!/usr/bin/env python3
"""C004 - does the C001 companion hold up beside many different large models? Registered in PREREG.md.

  python experiments/C004_model_sweep/run.py [--models MODELS.txt] [--seed 1] [--jsonl OUT.jsonl] [--oracle]

Each model is first given a qualifying probe (one plain lookup on a tiny log; it must answer correctly within
16 tokens). A model that fails the probe, or that the API will not serve, is reported and not scored. Qualifying
models run C001's four arms on the frozen C001 task.
"""
import argparse
import re
import json
import os
import platform
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "C001_context_economy"))
import run as c001  # noqa: E402
from companion.llm import NimModel, OracleModel  # noqa: E402
from companion.runtime import PROMPT  # noqa: E402
from task import make_task  # noqa: E402

PROBE_CTX = "P01 pressure 41\nP02 temperature 77\nP03 status RUNNING"
PROBE_Q, PROBE_A = "What is the temperature of P02?", "77"


def load_models(path):
    with open(path, encoding="utf-8") as fh:
        return [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]


def sweep_one(name, model, seed):
    try:
        text, _, _ = model.complete(PROMPT.format(context=PROBE_CTX, question=PROBE_Q))
    except SystemExit as exc:
        return {"model": name, "status": "COULD NOT RUN", "reason": str(exc)[:160]}
    if not c001.correct(text, PROBE_A):
        return {"model": name, "status": "DID NOT QUALIFY", "reason": f"probe answer {text[:40]!r}"}
    lines, asks = make_task(seed)
    out = {"model": name, "status": "RAN"}
    try:
        for arm in ("BASELINE", "COMPANION", "N1-NO-ESCALATION", "N2-RANDOM-DROP"):
            t0 = time.perf_counter()
            r = c001.summarise(c001.run_arm(arm, model, lines, asks, np.random.default_rng(seed + 7)))
            r["wall_seconds"] = time.perf_counter() - t0
            out[arm] = r
    except SystemExit as exc:
        return {"model": name, "status": "COULD NOT RUN", "reason": "mid-run: " + str(exc)[:140]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=os.path.join(HERE, "MODELS.txt"))
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--jsonl", default=None)
    ap.add_argument("--oracle", action="store_true")
    ap.add_argument("--serving-probe", default=None, metavar="OUT",
                    help="only send the one-question probe to every listed model and write the ones that answer "
                         "correctly to OUT (no scoring); C004b freezes its model list from this file")
    a = ap.parse_args()
    if a.serving_probe:
        good = []
        for name in load_models(a.models):
            try:
                text, _, _ = NimModel(name).complete(PROMPT.format(context=PROBE_CTX, question=PROBE_Q))
                status = "SERVES+ANSWERS" if c001.correct(text, PROBE_A) else f"SERVES, NO USABLE ANSWER ({text[:30]!r})"
            except SystemExit as exc:
                m = re.search(r"HTTP Error (\d+)[^)]*", str(exc))  # the HTTP code, not the hint text after it
                status = "NOT SERVED: " + (m.group(0) if m else str(exc)[:60])
            print(f"{name:46} {status}", flush=True)
            if status == "SERVES+ANSWERS":
                good.append(name)
        with open(a.serving_probe, "w", encoding="utf-8") as fh:
            fh.write("# models that answered the probe on " + __import__("time").strftime("%Y-%m-%d") + "\n")
            fh.write("\n".join(good) + "\n")
        print(f"{len(good)} models serve and answer; written to {a.serving_probe}")
        return
    names = ["oracle-test-double"] if a.oracle else load_models(a.models)
    print(f"VERITAS-COMPANION C004 | seed {a.seed} | {len(names)} models | {platform.machine()} | "
          f"Python {platform.python_version()}" + ("   *** ORACLE: NOT A RESULT ***" if a.oracle else ""))
    print(f"{'model':46} {'status':15} {'base acc':>8} {'comp acc':>8} {'gain':>6} {'base lkp':>8}")
    rows = []
    for name in names:
        print(f"... {name}", file=sys.stderr, flush=True)
        model = OracleModel() if a.oracle else NimModel(name)
        r = sweep_one(name, model, a.seed)
        rows.append(r)
        if a.jsonl:
            with open(a.jsonl, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
        if r["status"] == "RAN":
            b, c = r["BASELINE"], r["COMPANION"]
            print(f"{name:46} {'RAN':15} {b['accuracy']:8.4f} {c['accuracy']:8.4f} "
                  f"{b['large_tokens'] / max(1, c['large_tokens']):6.2f} {b['by_kind']['lookup']:8.4f}", flush=True)
        else:
            print(f"{name:46} {r['status']:15} {r['reason']}", flush=True)
    ran = [r for r in rows if r["status"] == "RAN"]
    if ran:
        gains = [r["BASELINE"]["large_tokens"] / max(1, r["COMPANION"]["large_tokens"]) for r in ran]
        within = sum(r["COMPANION"]["accuracy"] >= r["BASELINE"]["accuracy"] - 0.10 + 1e-12 for r in ran)
        diffs = [r["COMPANION"]["accuracy"] - r["BASELINE"]["accuracy"] for r in ran]
        print(f"qualified and ran: {len(ran)} of {len(rows)}; gain min {min(gains):.2f}; companion within one "
              f"question of baseline on {within}/{len(ran)}; median accuracy difference {np.median(diffs):+.4f}")


if __name__ == "__main__":
    main()

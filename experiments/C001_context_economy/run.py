#!/usr/bin/env python3
"""C001 - does the companion cut the large model's tokens without losing accuracy?

  python experiments/C001_context_economy/run.py --seed 101 [--server http://127.0.0.1:8080] [--oracle] [--json F]

--oracle uses a rule-based test double instead of a model: its numbers are NOT A RESULT.
"""
import argparse
import json
import os
import platform
import re
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from companion import Companion  # noqa: E402
from companion.llm import LlamaServer, OracleModel  # noqa: E402
from companion.runtime import PROMPT  # noqa: E402
from task import make_task  # noqa: E402


def correct(answer, expected):
    return re.search(rf"(?<![\w.]){re.escape(expected)}(?![\w.])", answer, re.IGNORECASE) is not None


def run_arm(name, model, lines, asks, rng):
    if name == "BASELINE":
        out = []
        for i, (q, exp, kind) in enumerate(asks):
            text, pt, ct = model.complete(PROMPT.format(context="\n".join(lines), question=q))
            out.append((kind, correct(text, exp), pt, ct, "large_model"))
        return out
    if name == "N2-RANDOM-DROP":
        drop = len(lines) - len(Companion.dedup(lines))
        keep = sorted(rng.choice(len(lines), len(lines) - drop, replace=False))
        lines, comp = [lines[i] for i in keep], Companion(model, dedup=False)
    else:
        comp = Companion(model, escalate_on_conflict=(name != "N1-NO-ESCALATION"))
    out = []
    for i, (q, exp, kind) in enumerate(asks):
        r = comp.ask(f"{name}-{i}", q, lines)
        out.append((kind, correct(r.final_result, exp), r.large_prompt_tokens, r.large_completion_tokens,
                    r.delegated_to))
    return out


def summarise(rows):
    tok = sum(pt + ct for _, _, pt, ct, _ in rows)
    acc = float(np.mean([ok for _, ok, *_ in rows]))
    by = {k: float(np.mean([ok for kd, ok, *_ in rows if kd == k])) for k in ("lookup", "conflict", "aggregate")}
    tiers = {t: sum(1 for *_, d in rows if d == t) for t in ("cache", "deterministic", "large_model")}
    return {"large_tokens": tok, "accuracy": acc, "by_kind": by, "tiers": tiers}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--server", default="http://127.0.0.1:8080")
    ap.add_argument("--oracle", action="store_true")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    model = OracleModel() if a.oracle else LlamaServer(a.server)
    lines, asks = make_task(a.seed)
    arms = ("BASELINE", "COMPANION", "N1-NO-ESCALATION", "N2-RANDOM-DROP")
    res = {}
    for n in arms:
        t0 = time.perf_counter()
        res[n] = summarise(run_arm(n, model, lines, asks, np.random.default_rng(a.seed + 7)))
        res[n]["wall_seconds"] = time.perf_counter() - t0  # everything: companion overhead and model calls
    base = res["BASELINE"]["large_tokens"]
    print(f"VERITAS-COMPANION C001 | seed {a.seed} | {platform.machine()} | Python {platform.python_version()}")
    print(f"model: {model.model_id()}" + ("   *** ORACLE TEST DOUBLE: NOT A RESULT ***" if not model.is_real else ""))
    print(f"log: {len(lines)} lines, {len(Companion.dedup(lines))} after dedup; {len(asks)} questions "
          f"({len(set(q for q, *_ in asks))} unique)")
    print(f"{'arm':18} {'large tok':>10} {'gain':>7} {'acc':>7} {'lookup':>7} {'conflict':>9} {'aggr':>6} "
          f"{'cache':>6} {'determ':>7} {'large':>6} {'wall s':>7}")
    for n in arms:
        r = res[n]
        gain = base / r["large_tokens"] if r["large_tokens"] else float("inf")
        print(f"{n:18} {r['large_tokens']:10d} {gain:7.2f} {r['accuracy']:7.4f} {r['by_kind']['lookup']:7.4f} "
              f"{r['by_kind']['conflict']:9.4f} {r['by_kind']['aggregate']:6.4f} {r['tiers']['cache']:6d} "
              f"{r['tiers']['deterministic']:7d} {r['tiers']['large_model']:6d} {r['wall_seconds']:7.1f}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"experiment": "C001", "seed": a.seed, "model": model.model_id(), "real_model": model.is_real,
                       "machine": platform.machine(), "arms": res}, fh, indent=1, sort_keys=True)


if __name__ == "__main__":
    main()

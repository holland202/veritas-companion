#!/usr/bin/env python3
"""C002 - the C001 companion on a real log nobody built for it.

  python experiments/C002_real_log/run.py --log ~/llama-server.log --seed 101 [--server URL] [--oracle] [--json F]

A window of the log is taken (seeded), and questions are made from its `key = value` lines: keys with one
value are lookups; keys whose value changes are conflicts, whose answer is the last value in the window.
--oracle uses a rule-based test double: NOT A RESULT.
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
from companion import Companion  # noqa: E402
from companion.kv import parse_kv  # noqa: E402
from companion.llm import LlamaServer, OracleModel  # noqa: E402
from companion.runtime import PROMPT  # noqa: E402

WINDOW, MAX_CHARS, TOKEN_LIMIT, N_LOOKUP, N_CONFLICT = 150, 200, 3500, 5, 3


def facts(lines):
    by = {}
    for ln in lines:
        kv = parse_kv(ln)
        if kv:
            by.setdefault(kv[0], []).append(kv[1])
    single = sorted(k for k, v in by.items() if len(set(v)) == 1)
    multi = sorted(k for k, v in by.items() if len(set(v)) > 1)
    return by, single, multi


def make_task(all_lines, seed, model, asks_each=1, max_tries=400):
    """Seeded order of window starts; the first window that still holds enough facts of both kinds once it
    is trimmed to fit the model's context is used. A window that fails is skipped, not repaired."""
    rng = np.random.default_rng(seed)
    lines = [ln.rstrip("\n")[:MAX_CHARS] for ln in all_lines if ln.strip()]
    tried = 0
    for s in rng.permutation(max(1, len(lines) - WINDOW + 1)):
        win = lines[s:s + WINDOW]
        by, single, multi = facts(win)
        if len(single) < N_LOOKUP or len(multi) < N_CONFLICT:
            continue
        tried += 1
        if tried > max_tries:
            break
        while win and len("\n".join(win)) > 4 * TOKEN_LIMIT:  # cheap trim by characters before asking the tokenizer
            win = win[:-5]
        while win and model.count_tokens(PROMPT.format(context="\n".join(win), question="x" * 40)) > TOKEN_LIMIT:
            win = win[:-5]
        by, single, multi = facts(win)
        if len(single) >= N_LOOKUP and len(multi) >= N_CONFLICT:
            break
    else:
        raise SystemExit("COULD NOT RUN: no window of this log holds enough facts of both kinds within the context")
    if tried > max_tries:
        raise SystemExit(f"COULD NOT RUN: {max_tries} eligible windows tried; none fits the context with enough facts")
    qs = [(f"What is the value of {k}?", by[k][0], "lookup") for k in rng.choice(single, N_LOOKUP, replace=False)]
    qs += [(f"What is the value of {k}?", by[k][-1], "conflict") for k in rng.choice(multi, N_CONFLICT, replace=False)]
    asks = [q for q in qs for _ in range(asks_each)]
    return int(s), win, [asks[i] for i in rng.permutation(len(asks))]


def correct(answer, expected):
    return re.search(rf"(?<![\w.]){re.escape(expected)}(?![\w.])", answer, re.IGNORECASE) is not None


def run_arm(name, model, lines, asks, rng):
    rows = []
    if name == "BASELINE":
        for q, exp, kind in asks:
            text, pt, ct = model.complete(PROMPT.format(context="\n".join(lines), question=q))
            rows.append((kind, correct(text, exp), pt, ct, "large_model"))
        return rows
    if name == "N2-RANDOM-DROP":
        drop = len(lines) - len(Companion.dedup(lines))
        keep = sorted(rng.choice(len(lines), len(lines) - drop, replace=False))
        lines, comp = [lines[i] for i in keep], Companion(model, dedup=False)
    else:
        comp = Companion(model, escalate_on_conflict=(name != "N1-NO-ESCALATION"))
    for i, (q, exp, kind) in enumerate(asks):
        r = comp.ask(f"{name}-{i}", q, lines)
        rows.append((kind, correct(r.final_result, exp), r.large_prompt_tokens, r.large_completion_tokens,
                     r.delegated_to))
    return rows


def summarise(rows):
    return {"large_tokens": sum(pt + ct for _, _, pt, ct, _ in rows),
            "accuracy": float(np.mean([ok for _, ok, *_ in rows])),
            "by_kind": {k: float(np.mean([ok for kd, ok, *_ in rows if kd == k])) for k in ("lookup", "conflict")},
            "tiers": {t: sum(1 for *_, d in rows if d == t) for t in ("cache", "deterministic", "large_model")}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--server", default="http://127.0.0.1:8080")
    ap.add_argument("--oracle", action="store_true")
    ap.add_argument("--json", default=None)
    ap.add_argument("--asks", type=int, default=1, help="times each question is asked (repeats go to the cache)")
    ap.add_argument("--keys-only", action="store_true", help="print question keys without their values (for logs "
                    "that may hold personal data, such as logcat)")
    ap.add_argument("--probe", action="store_true", help="only report what the log offers; no model needed")
    a = ap.parse_args()
    if a.probe:
        with open(os.path.expanduser(a.log), encoding="utf-8", errors="replace") as fh:
            lines = [ln.rstrip("\n")[:MAX_CHARS] for ln in fh if ln.strip()]
        by, single, multi = facts(lines)
        ok = sum(1 for s in range(0, max(1, len(lines) - WINDOW + 1), 10)
                 if (lambda f: len(f[1]) >= N_LOOKUP and len(f[2]) >= N_CONFLICT)(facts(lines[s:s + WINDOW])))
        print(f"PROBE {a.log}: {len(lines)} lines, {len(Companion.dedup(lines))} distinct; "
              f"{sum(len(v) for v in by.values())} key=value lines, {len(single)} single-valued keys, "
              f"{len(multi)} changing keys; usable {WINDOW}-line windows (every 10th start): {ok}")
        print("single e.g.: " + ", ".join(single[:8]))
        print("changing e.g.: " + ", ".join(multi[:8]))
        return
    model = OracleModel() if a.oracle else LlamaServer(a.server)
    with open(os.path.expanduser(a.log), encoding="utf-8", errors="replace") as fh:
        all_lines = fh.readlines()
    start, lines, asks = make_task(all_lines, a.seed, model, a.asks)
    arms = ("BASELINE", "COMPANION", "N1-NO-ESCALATION", "N2-RANDOM-DROP")
    res = {}
    for n in arms:
        print(f"running {n} ...", file=sys.stderr, flush=True)
        t0 = time.perf_counter()
        res[n] = summarise(run_arm(n, model, lines, asks, np.random.default_rng(a.seed + 7)))
        res[n]["wall_seconds"] = time.perf_counter() - t0
    base = res["BASELINE"]["large_tokens"]
    print(f"VERITAS-COMPANION C002 | seed {a.seed} | {platform.machine()} | Python {platform.python_version()}")
    print(f"model: {model.model_id()}" + ("   *** ORACLE TEST DOUBLE: NOT A RESULT ***" if not model.is_real else ""))
    print(f"log: {os.path.basename(a.log)}, {len(all_lines)} lines; window at line {start}: {len(lines)} lines, "
          f"{len(Companion.dedup(lines))} after dedup; {len(asks)} questions ({len(set(q for q, *_ in asks))} unique)")
    removed = len(lines) - len(Companion.dedup(lines))
    print(f"asks per question {a.asks}; exact-line dedup removes {removed} of {len(lines)} window lines"
          + ("   (N2 is VACUOUS here: nothing to drop, so it equals COMPANION by construction)" if removed == 0 else ""))
    print("questions: " + "; ".join(sorted({(f'{q[21:-1]} ({k})' if a.keys_only else f'{q[21:-1]} -> {e} ({k})')
                                            for q, e, k in asks})))
    print(f"{'arm':18} {'large tok':>10} {'gain':>7} {'acc':>7} {'lookup':>7} {'conflict':>9} "
          f"{'cache':>6} {'determ':>7} {'large':>6} {'wall s':>7}")
    for n in arms:
        r = res[n]
        gain = base / r["large_tokens"] if r["large_tokens"] else float("inf")
        print(f"{n:18} {r['large_tokens']:10d} {gain:7.2f} {r['accuracy']:7.4f} {r['by_kind']['lookup']:7.4f} "
              f"{r['by_kind']['conflict']:9.4f} {r['tiers']['cache']:6d} {r['tiers']['deterministic']:7d} "
              f"{r['tiers']['large_model']:6d} {r['wall_seconds']:7.1f}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"experiment": "C002", "seed": a.seed, "log": a.log, "window_start": start, "model": model.model_id(),
                       "real_model": model.is_real, "arms": res}, fh, indent=1, sort_keys=True)


if __name__ == "__main__":
    main()

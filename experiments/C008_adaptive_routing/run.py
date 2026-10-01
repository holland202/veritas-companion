#!/usr/bin/env python3
"""C008 -- Adaptive Tier Routing (Tier-0 -> Tier-1 -> Tier-2).

  python experiments/C008_adaptive_routing/run.py --seed 101 [--oracle] [--json F]

Without a real small-model backend the Tier-1 path uses AlwaysEscalateTier1 (fail-closed
stub). Numbers produced with the stub or with --oracle are plumbing checks, NOT RESULTS.

Arms:
  B0  large-model only
  B1  existing companion (Tier-0 -> Tier-2)
  B2  adaptive cascade   (Tier-0 -> Tier-1 -> Tier-2)
  N1  Tier-1 forced answer (no escalation) -- only meaningful with a real Tier-1

False-accept tracking: a Tier-1 SUPPORTED answer that is wrong vs the task truth, and
that was accepted (delegated_to == "tier1").
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(HERE, "..", "C003_routing_ladder"))

from companion import Companion, AlwaysEscalateTier1  # noqa: E402
from companion.llm import LlamaServer, OracleModel  # noqa: E402
from companion.runtime import PROMPT  # noqa: E402
from companion.tier1 import Tier1Result, parse_tier1_output  # noqa: E402
from task import make_task  # noqa: E402


def correct(answer, expected):
    if expected is None or answer is None:
        return False
    return re.search(rf"(?<![\w.]){re.escape(str(expected))}(?![\w.])", str(answer), re.IGNORECASE) is not None


class ForcedAnswerTier1:
    """N1 control: always emits SUPPORTED with a guess. Not a real model."""

    def model_id(self):
        return "tier1-forced-answer-control"

    def complete(self, prompt: str):
        ctx = prompt.split("Question:", 1)[0]
        tokens = re.findall(r"\b[\w.-]+\b", ctx)
        guess = tokens[-1] if tokens else "unknown"
        payload = json.dumps({
            "answer": guess,
            "status": "SUPPORTED",
            "evidence": [tokens[-1]] if tokens else [],
            "reason": "forced_n1_control",
            "should_escalate": False,
        })
        return payload, len(prompt.split()), 1


def run_b0(model, lines, qs):
    rows = []
    for i, q in enumerate(qs):
        t0 = time.perf_counter()
        text, pt, ct = model.complete(PROMPT.format(context="\n".join(lines), question=q["q"]))
        ok = correct(text, q.get("truth"))
        rows.append({
            "task_id": f"B0-{i}", "kind": q.get("kind", ""), "expect": q.get("expect"),
            "truth": q.get("truth"), "delegated_to": "large_model", "status": "ESCALATE",
            "final": text, "ok": ok, "false_accept": False, "pt": pt, "ct": ct,
            "seconds": time.perf_counter() - t0,
        })
    return rows


def run_companion(name, model, lines, qs, tier1=None, escalate_on_conflict=True):
    comp = Companion(model, escalate_on_conflict=escalate_on_conflict, tier1=tier1)
    rows = []
    for i, q in enumerate(qs):
        r = comp.ask(f"{name}-{i}", q["q"], lines)
        ok = correct(r.final_result, q.get("truth"))
        false_accept = (r.delegated_to == "tier1" and r.status == "SUPPORTED" and not ok)
        rows.append({
            "task_id": r.task_id, "kind": q.get("kind", ""), "expect": q.get("expect"),
            "truth": q.get("truth"), "delegated_to": r.delegated_to, "status": r.status,
            "final": r.final_result, "ok": ok, "false_accept": false_accept,
            "pt": r.large_prompt_tokens, "ct": r.large_completion_tokens,
            "seconds": r.companion_seconds, "cached_origin": r.cached_origin,
        })
    return rows, comp


def summarise(arm, rows):
    n = len(rows)
    ok_n = sum(1 for r in rows if r["ok"])
    fa = sum(1 for r in rows if r["false_accept"])
    tok = sum(r["pt"] + r["ct"] for r in rows)
    by_tier = {}
    for r in rows:
        by_tier[r["delegated_to"]] = by_tier.get(r["delegated_to"], 0) + 1
    return {
        "arm": arm, "n": n, "verified_ok": ok_n,
        "accuracy": ok_n / n if n else 0.0,
        "false_accept": fa, "false_accept_rate": fa / n if n else 0.0,
        "total_tokens": tok,
        "cost_per_verified": (tok / ok_n) if ok_n else None,
        "by_tier": by_tier,
        "tier2_calls": by_tier.get("large_model", 0),
        "tier1_calls": by_tier.get("tier1", 0),
        "tier0_calls": by_tier.get("deterministic", 0) + by_tier.get("cache", 0),
    }


def main():
    ap = argparse.ArgumentParser(description="C008 adaptive tier routing")
    ap.add_argument("--seed", type=int, default=101)
    ap.add_argument("--oracle", action="store_true", help="use OracleModel (NOT A RESULT)")
    ap.add_argument("--server", default="http://127.0.0.1:8080")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    lines, tags, qs = make_task(a.seed)
    model = OracleModel() if a.oracle else LlamaServer(url=a.server, seed=a.seed)

    print(f"VERITAS-COMPANION C008 | seed {a.seed} | {platform.machine()} | Python {platform.python_version()}")
    print(f"model: {model.model_id()}")
    print(f"tier1: AlwaysEscalateTier1 (stub -- no small model wired)")
    print(f"log: {len(lines)} lines; {len(qs)} questions")
    print()

    results = {}
    rows_b0 = run_b0(model, lines, qs)
    results["B0"] = summarise("B0", rows_b0)
    rows_b1, _ = run_companion("B1", model, lines, qs, tier1=None)
    results["B1"] = summarise("B1", rows_b1)
    rows_b2, _ = run_companion("B2", model, lines, qs, tier1=AlwaysEscalateTier1())
    results["B2"] = summarise("B2", rows_b2)
    rows_n1, _ = run_companion("N1", model, lines, qs, tier1=ForcedAnswerTier1())
    results["N1"] = summarise("N1", rows_n1)

    print(f"{'arm':<6} {'tok':>8} {'acc':>7} {'fa':>4} {'t0':>4} {'t1':>4} {'t2':>4} {'cost/ok':>10}")
    for arm in ("B0", "B1", "B2", "N1"):
        s = results[arm]
        cost = f"{s['cost_per_verified']:.1f}" if s["cost_per_verified"] is not None else "--"
        print(f"{arm:<6} {s['total_tokens']:>8} {s['accuracy']:>7.4f} {s['false_accept']:>4} "
              f"{s['tier0_calls']:>4} {s['tier1_calls']:>4} {s['tier2_calls']:>4} {cost:>10}")

    print()
    print("NOTE: Tier-1 is the always-escalate stub. B2 must match B1 on tokens/accuracy.")
    print("      A real small-model backend is required before any efficiency claim.")
    print("      Numbers with --oracle are NOT A RESULT.")

    out = {
        "experiment": "C008", "seed": a.seed, "model": model.model_id(),
        "tier1": "AlwaysEscalateTier1", "platform": platform.platform(),
        "python": platform.python_version(), "n_lines": len(lines),
        "n_questions": len(qs), "summary": results,
        "rows": {"B0": rows_b0, "B1": rows_b1, "B2": rows_b2, "N1": rows_n1},
    }
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, sort_keys=True)
        print(f"wrote {a.json}")

    if results["B1"]["tier2_calls"] != results["B2"]["tier2_calls"]:
        print("PLUMBING FAIL: B1/B2 tier2_calls differ under AlwaysEscalateTier1")
        sys.exit(1)
    if abs(results["B1"]["accuracy"] - results["B2"]["accuracy"]) > 1e-9:
        print("PLUMBING FAIL: B1/B2 accuracy differ under AlwaysEscalateTier1")
        sys.exit(1)
    print("PLUMBING PASS (B1 == B2 under escalate-stub)")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)

#!/usr/bin/env python3
"""C008 -- Adaptive Tier Routing (Tier-0 -> Tier-1 -> Tier-2).

  # Plumbing only (Oracle; NOT A RESULT):
  python experiments/C008_adaptive_routing/run.py --seed 101 --oracle

  # Real Tier-1 pilot (local llama.cpp on :8081) + Tier-2 on :8080:
  python experiments/C008_adaptive_routing/run.py --seed 101 \\
      --tier1-server http://127.0.0.1:8081 --tier1-model qwen2.5-0.5b-instruct-q4_k_m.gguf

Without --tier1-server the cascade uses AlwaysEscalateTier1 (fail-closed stub).
Oracle path is PLUMBING ONLY / NOT A RESULT. Pilot runs are NOT registered evaluation.

Arms:
  B0  large-model only
  B1  existing companion (Tier-0 -> Tier-2)
  B2  adaptive cascade   (Tier-0 -> Tier-1 -> Tier-2)
  N1  Tier-1 forced answer (exposes escalation protection)

false_accept = Tier-1 SUPPORTED answer that is wrong vs task truth and was accepted.
token_cost_per_correct_task = total model tokens (Tier-1 + Tier-2) / number of correct answers.
\"Correct\" means answer matched task truth — not a synonym for \"verified\" in the gate sense.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(HERE, "..", "C003_routing_ladder"))

from companion import Companion, AlwaysEscalateTier1, LlamaServerTier1  # noqa: E402
from companion.llm import LlamaServer, OracleModel  # noqa: E402
from companion.runtime import PROMPT  # noqa: E402
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
            "final": text, "ok": ok, "false_accept": False,
            "pt": pt, "ct": ct, "tier1_pt": 0, "tier1_ct": 0, "tier2_pt": pt, "tier2_ct": ct,
            "seconds": time.perf_counter() - t0, "evidence": None,
        })
    return rows


def run_companion(name, model, lines, qs, tier1=None, escalate_on_conflict=True):
    comp = Companion(model, escalate_on_conflict=escalate_on_conflict, tier1=tier1)
    rows = []
    for i, q in enumerate(qs):
        r = comp.ask(f"{name}-{i}", q["q"], lines)
        ok = correct(r.final_result, q.get("truth"))
        false_accept = (r.delegated_to == "tier1" and r.status == "SUPPORTED" and not ok)
        pt, ct = r.large_prompt_tokens, r.large_completion_tokens
        if r.delegated_to == "tier1":
            t1_pt, t1_ct, t2_pt, t2_ct = pt, ct, 0, 0
        elif r.delegated_to == "large_model":
            t1_pt, t1_ct, t2_pt, t2_ct = 0, 0, pt, ct
        else:
            t1_pt, t1_ct, t2_pt, t2_ct = 0, 0, 0, 0
        rows.append({
            "task_id": r.task_id, "kind": q.get("kind", ""), "expect": q.get("expect"),
            "truth": q.get("truth"), "delegated_to": r.delegated_to, "status": r.status,
            "final": r.final_result, "ok": ok, "false_accept": false_accept,
            "pt": pt, "ct": ct,
            "tier1_pt": t1_pt, "tier1_ct": t1_ct, "tier2_pt": t2_pt, "tier2_ct": t2_ct,
            "seconds": r.companion_seconds, "cached_origin": r.cached_origin,
            "evidence": getattr(r, "evidence", None),
        })
    return rows, comp


def summarise(arm, rows):
    n = len(rows)
    ok_n = sum(1 for r in rows if r["ok"])
    fa = sum(1 for r in rows if r["false_accept"])
    t1_pt = sum(r["tier1_pt"] for r in rows)
    t1_ct = sum(r["tier1_ct"] for r in rows)
    t2_pt = sum(r["tier2_pt"] for r in rows)
    t2_ct = sum(r["tier2_ct"] for r in rows)
    total_tok = t1_pt + t1_ct + t2_pt + t2_ct
    by_tier = {}
    for r in rows:
        by_tier[r["delegated_to"]] = by_tier.get(r["delegated_to"], 0) + 1
    t1_accepted = by_tier.get("tier1", 0)
    wall = sum(r["seconds"] for r in rows)
    return {
        "arm": arm,
        "n": n,
        "correct": ok_n,
        "accuracy": ok_n / n if n else 0.0,
        "false_accept_count": fa,
        "false_accept_rate": fa / n if n else 0.0,
        "total_tokens": total_tok,
        "tier1_prompt_tokens": t1_pt,
        "tier1_completion_tokens": t1_ct,
        "tier2_prompt_tokens": t2_pt,
        "tier2_completion_tokens": t2_ct,
        "token_cost_per_correct_task": (total_tok / ok_n) if ok_n else None,
        "by_tier": by_tier,
        "tier0_calls": by_tier.get("deterministic", 0) + by_tier.get("cache", 0),
        "tier1_accepted": t1_accepted,
        "tier2_calls": by_tier.get("large_model", 0),
        "wall_seconds": wall,
    }


def main():
    ap = argparse.ArgumentParser(description="C008 adaptive tier routing")
    ap.add_argument("--seed", type=int, default=101)
    ap.add_argument("--oracle", action="store_true", help="use OracleModel (PLUMBING ONLY / NOT A RESULT)")
    ap.add_argument("--server", default="http://127.0.0.1:8080", help="Tier-2 llama.cpp URL")
    ap.add_argument("--tier1-server", default=None,
                    help="Tier-1 llama.cpp URL (default: none → AlwaysEscalateTier1 stub)")
    ap.add_argument("--tier1-model", default=None,
                    help="expected Tier-1 model basename/path; mismatch fails closed")
    ap.add_argument("--tier1-predict", type=int, default=96, help="Tier-1 n_predict (structured JSON)")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    lines, tags, qs = make_task(a.seed)
    model = OracleModel() if a.oracle else LlamaServer(url=a.server, seed=a.seed)

    if a.tier1_server:
        tier1 = LlamaServerTier1(
            url=a.tier1_server,
            n_predict=a.tier1_predict,
            seed=a.seed,
            expected_model=a.tier1_model,
        )
        tier1_label = tier1.model_id()
    else:
        tier1 = AlwaysEscalateTier1()
        tier1_label = tier1.model_id()

    print(f"VERITAS-COMPANION C008 | seed {a.seed} | {platform.machine()} | Python {platform.python_version()}")
    print(f"tier2: {model.model_id()}")
    print(f"tier1: {tier1_label}")
    if a.oracle:
        print("MODE: ORACLE — PLUMBING ONLY / NOT A RESULT")
    print(f"log: {len(lines)} lines; {len(qs)} questions")
    print()

    results = {}
    rows_b0 = run_b0(model, lines, qs)
    results["B0"] = summarise("B0", rows_b0)
    rows_b1, _ = run_companion("B1", model, lines, qs, tier1=None)
    results["B1"] = summarise("B1", rows_b1)
    rows_b2, _ = run_companion("B2", model, lines, qs, tier1=tier1)
    results["B2"] = summarise("B2", rows_b2)
    rows_n1, _ = run_companion("N1", model, lines, qs, tier1=ForcedAnswerTier1())
    results["N1"] = summarise("N1", rows_n1)

    b0_t2 = results["B0"]["tier2_calls"] or 1
    for arm in results:
        results[arm]["large_model_avoidance"] = 1.0 - (results[arm]["tier2_calls"] / b0_t2)

    hdr = (f"{'arm':<6} {'tok':>8} {'acc':>7} {'fa':>4} "
           f"{'t0':>4} {'t1a':>4} {'t2':>4} {'t1tok':>7} {'t2tok':>7} {'$/ok':>10}")
    print(hdr)
    for arm in ("B0", "B1", "B2", "N1"):
        s = results[arm]
        cost = f"{s['token_cost_per_correct_task']:.1f}" if s["token_cost_per_correct_task"] is not None else "—"
        t1tok = s["tier1_prompt_tokens"] + s["tier1_completion_tokens"]
        t2tok = s["tier2_prompt_tokens"] + s["tier2_completion_tokens"]
        print(f"{arm:<6} {s['total_tokens']:>8} {s['accuracy']:>7.4f} {s['false_accept_count']:>4} "
              f"{s['tier0_calls']:>4} {s['tier1_accepted']:>4} {s['tier2_calls']:>4} "
              f"{t1tok:>7} {t2tok:>7} {cost:>10}")

    print()
    if a.tier1_server is None:
        print("NOTE: Tier-1 is AlwaysEscalateTier1 (no --tier1-server). B2 must match B1.")
    else:
        print(f"NOTE: Tier-1 is live at {a.tier1_server} ({tier1_label}). Pilot only — NOT A REGISTERED RESULT.")
    if a.oracle:
        print("      ORACLE path: PLUMBING ONLY / NOT A RESULT.")

    out = {
        "experiment": "C008",
        "seed": a.seed,
        "tier2_model": model.model_id(),
        "tier1_model": tier1_label,
        "tier1_server": a.tier1_server,
        "oracle": a.oracle,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "n_lines": len(lines),
        "n_questions": len(qs),
        "summary": results,
        "rows": {"B0": rows_b0, "B1": rows_b1, "B2": rows_b2, "N1": rows_n1},
    }
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, sort_keys=True)
        print(f"wrote {a.json}")

    if a.tier1_server is None:
        if results["B1"]["tier2_calls"] != results["B2"]["tier2_calls"]:
            print("PLUMBING FAIL: B1/B2 tier2_calls differ under AlwaysEscalateTier1")
            sys.exit(1)
        if abs(results["B1"]["accuracy"] - results["B2"]["accuracy"]) > 1e-9:
            print("PLUMBING FAIL: B1/B2 accuracy differ under AlwaysEscalateTier1")
            sys.exit(1)
        print("PLUMBING PASS (B1 ≡ B2 under escalate-stub)")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)

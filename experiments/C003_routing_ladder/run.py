#!/usr/bin/env python3
"""C003 - does tier 0 know when to answer, when to flag, and when to hand off; and does it keep the evidence?

  python experiments/C003_routing_ladder/run.py --seed 101 [--model | --oracle] [--json F]

Without --model the run is deterministic (no language model): routing, answers, traps and evidence survival.
"""
import argparse
import json
import os
import platform
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from companion import Companion  # noqa: E402
from companion.llm import LlamaServer, OracleModel  # noqa: E402
from companion.runtime import PROMPT  # noqa: E402
from task import make_task  # noqa: E402


def naive_answer(lines, q):
    """The null tier 0: first line that mentions the asset and the field word, anywhere. No conflict check."""
    m = re.match(r"What is the (\w+) of (P\d+)\?", q)
    if not m:
        return None
    for ln in lines:
        if m.group(2) in ln and m.group(1) in ln:
            return ln.split()[-1]
    return None


def evidence_kept(tags_kept, need):
    have = set().union(*tags_kept) if tags_kept else set()
    return need <= have


def correct(ans, truth):
    return truth is not None and ans is not None and re.search(rf"(?<![\w.]){re.escape(truth)}(?![\w.])", ans, re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--model", action="store_true", help="also run the language-model arms on a local llama-server")
    ap.add_argument("--oracle", action="store_true")
    ap.add_argument("--server", default="http://127.0.0.1:8080")
    ap.add_argument("--expect-model", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    lines, tags, qs = make_task(a.seed)
    comp = Companion(OracleModel())
    ded = Companion.dedup(lines)
    removed = len(lines) - len(ded)
    kept_idx = []
    seen = set()
    for i, ln in enumerate(lines):
        if ln not in seen:
            seen.add(ln); kept_idx.append(i)
    rng = np.random.default_rng(a.seed + 7)
    drop_idx = sorted(rng.choice(len(lines), len(lines) - removed, replace=False))
    rows = []
    for q in qs:
        r = comp.cheap_answer(ded, q["q"])
        nv = naive_answer(lines, q["q"])
        rows.append(dict(kind=q["kind"], expect=q["expect"], status=r.status,
                         routed_ok=r.status == q["expect"],
                         answer_ok=(r.status != "SUPPORTED") or bool(correct(r.value, q["truth"])),
                         false_supported=q["expect"] == "UNCERTAIN" and r.status == "SUPPORTED",
                         naive_wrong=(q["kind"].startswith("L0") and (q["truth"] is None or not correct(nv, q["truth"]))),
                         kept_dedup=evidence_kept([tags[i] for i in kept_idx], q["need"]),
                         kept_random=evidence_kept([tags[i] for i in drop_idx], q["need"])))
    out = {"seed": a.seed, "lines": len(lines), "dedup_removed": removed, "questions": len(qs),
           "routing_ok": sum(r["routed_ok"] for r in rows), "answers_ok": sum(r["answer_ok"] for r in rows),
           "false_supported": sum(r["false_supported"] for r in rows),
           "naive_wrong_on_L0": sum(r["naive_wrong"] for r in rows),
           "L0_questions": sum(1 for r in rows if r["kind"].startswith("L0")),
           "evidence_kept_dedup": sum(r["kept_dedup"] for r in rows),
           "evidence_kept_random": sum(r["kept_random"] for r in rows),
           "by_kind": {k: [sum(r["routed_ok"] for r in rows if r["kind"] == k), sum(1 for r in rows if r["kind"] == k)]
                       for k in dict.fromkeys(r["kind"] for r in rows)}}
    print(f"VERITAS-COMPANION C003 | seed {a.seed} | {platform.machine()} | Python {platform.python_version()}")
    print(f"log {out['lines']} lines, dedup removes {removed}; {out['questions']} questions")
    print("routing by kind (correct/total): " + "; ".join(f"{k} {v[0]}/{v[1]}" for k, v in out["by_kind"].items()))
    print(f"routing correct {out['routing_ok']}/{out['questions']}; answers correct when SUPPORTED "
          f"{out['answers_ok']}/{out['questions']}; false SUPPORTED on planted conflicts {out['false_supported']}")
    print(f"null (naive first-match) wrong on L0 lookups: {out['naive_wrong_on_L0']}/{out['L0_questions']}")
    print(f"evidence each question needs still present: dedup {out['evidence_kept_dedup']}/{out['questions']}, "
          f"random drop of the same number of lines {out['evidence_kept_random']}/{out['questions']}")
    if a.model or a.oracle:
        model = OracleModel() if a.oracle else LlamaServer(a.server)
        if isinstance(model, LlamaServer):
            model.require_model(a.expect_model)
        base = comp2 = 0
        c = Companion(model)
        scored = [q for q in qs if q["truth"] is not None]
        for q in scored:
            text, _, _ = model.complete(PROMPT.format(context="\n".join(lines), question=q["q"]))
            base += bool(correct(text, q["truth"]))
            rr = c.ask("c3", q["q"], lines)
            comp2 += bool(correct(rr.final_result, q["truth"]))
        out["model_base_acc"], out["model_comp_acc"] = base / len(scored), comp2 / len(scored)
        print(f"model: {model.model_id()}  accuracy on the {len(scored)} answerable questions: "
              f"model alone {out['model_base_acc']:.4f}, with companion {out['model_comp_acc']:.4f}")
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""C006 (registered in PREREG.md): the companion and the gate on Loghub HDFS 2k.

  python experiments/C006_external_logs/fetch.py          # once; verifies the frozen hashes
  python experiments/C006_external_logs/run.py --sv ~/sovereign-veritas [--nim MODEL] [--json OUT]

Without --nim only the deterministic parts run (tier-0 tools, the gate, coverage, the shuffle control on
tool answers); the model arms (A0, and the model half of A1-A5) need --nim or are reported NOT RUN.
Questions are generated from Loghub's structured parse by the frozen templates and seed; the arms see
only the question text and the log lines, never the truth.
"""
import argparse, csv, hashlib, importlib.util, json, os, platform, re, sys, tempfile
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, ROOT)
from companion import Companion  # noqa: E402
from companion.llm import NimModel  # noqa: E402

DATA = os.path.join(ROOT, "data", "loghub_hdfs")
SEED, N_BLOCKS = 6, 20
BLK = re.compile(r"blk_-?\d+")


class NoModel:
    """Stands in for the large model when none is given: returns nothing. NOT A RESULT; model arms are NOT RUN."""
    is_real = False

    def model_id(self):
        return "no-model"

    def count_tokens(self, text):
        return len(text.split())

    def complete(self, prompt):
        return "", 0, 0


def load(sv, name, rel):
    s = importlib.util.spec_from_file_location(name, os.path.join(sv, rel))
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def questions():
    """60 questions from the frozen templates; truth from Loghub's structured parse."""
    rows = list(csv.DictReader(open(os.path.join(DATA, "HDFS_2k.log_structured.csv"), encoding="utf-8")))
    by_blk = defaultdict(list)
    for r in rows:
        for b in set(BLK.findall(r["Content"])):
            by_blk[b].append(r)
    eligible = sorted(b for b, rs in by_blk.items() if len(rs) >= 3)
    if len(eligible) < N_BLOCKS:
        dist = sorted(Counter(len(rs) for rs in by_blk.values()).items())
        print(f"COULD NOT RUN AS REGISTERED: {len(eligible)} blocks have >= 3 lines, the registration needs "
              f"{N_BLOCKS}. {len(rows)} rows, {len(by_blk)} distinct blocks; (lines per block, blocks): {dist}")
        sys.exit(3)
    pick = np.random.default_rng(SEED).choice(len(eligible), N_BLOCKS, replace=False)
    qs = []
    for i in sorted(pick):
        b = eligible[i]
        rs = sorted(by_blk[b], key=lambda r: int(r["LineId"]))
        qs.append({"kind": "last", "q": f"Which event template was logged last for block {b}?", "truth": rs[-1]["EventId"]})
        qs.append({"kind": "count", "q": f"How many lines mention block {b}?", "truth": str(len(rs))})
        qs.append({"kind": "first_component", "q": f"Which component logged the first line for block {b}?",
                   "truth": rs[0]["Component"]})
    return qs, len(eligible)


def correct(ans, truth):
    return ans is not None and re.search(rf"(?<![\w.-]){re.escape(truth)}(?![\w.])", str(ans)) is not None


def run_arm(name, lines, qs, model, ca, sv_tmp, escalate_on_conflict=True, tools=True):
    comp = Companion(model, escalate_on_conflict=escalate_on_conflict, log_path=os.path.join(sv_tmp, f"{name}.jsonl"))
    out = []
    for i, q in enumerate(qs):
        if tools:
            rec = comp.ask(f"{name}-{i}", q["q"], lines)
        else:
            text, pt, ct = model.complete(f"Log:\n" + "\n".join(lines) + f"\nQuestion: {q['q']}\nAnswer:")
            rec = type("R", (), {"status": "ESCALATE", "delegated_to": "large_model", "final_result": text,
                                 "cached_origin": None})()
        r = {"status": rec.status, "delegated_to": rec.delegated_to, "final_result": rec.final_result,
             "cached_origin": getattr(rec, "cached_origin", None)}
        pkg = ca.package_for(r, f"{name}:{i}", "normal", os.path.join(sv_tmp, "sandbox"))
        out.append({"kind": q["kind"], "status": rec.status, "decision": pkg["decision"]["decision"],
                    "ok": bool(correct(rec.final_result, q["truth"]))})
    return out


def summarize(rows):
    n = len(rows)
    sup = sum(r["status"] == "SUPPORTED" for r in rows)
    allow = [r for r in rows if r["decision"] == "ALLOW"]
    acc = {k: (sum(r["ok"] for r in rows if r["kind"] == k), sum(1 for r in rows if r["kind"] == k))
           for k in ("last", "count", "first_component")}
    return {"n": n, "supported": sup, "allowed": len(allow), "false_allow": sum(not r["ok"] for r in allow),
            "statuses": dict(Counter(r["status"] for r in rows)), "acc": acc}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sv", required=True)
    ap.add_argument("--nim", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    fetch = load(HERE, "c006_fetch", "fetch.py")
    for name, want in fetch.FROZEN.items():
        path = os.path.join(DATA, name)
        if not os.path.exists(path) or hashlib.sha256(open(path, "rb").read()).hexdigest() != want:
            print(f"COULD NOT RUN: {name} missing or not the frozen file; run fetch.py first")
            sys.exit(2)
    ca = load(os.path.expanduser(a.sv), "sv_companion_action", "tools/companion_action.py")
    qs, eligible = questions()
    lines = open(os.path.join(DATA, "HDFS_2k.log"), encoding="utf-8").read().splitlines()
    rng = np.random.default_rng(SEED)
    shuffled = [lines[i] for i in rng.permutation(len(lines))]
    ded = Companion.dedup(lines)
    drop = sorted(np.random.default_rng(SEED + 1).choice(len(lines), len(ded), replace=False))
    dropped = [lines[i] for i in drop]
    model = NimModel(a.nim) if a.nim else NoModel()
    tmp = tempfile.mkdtemp(prefix="c006_")
    arms = {
        "A1 companion": run_arm("A1", lines, qs, model, ca, tmp),
        "A2 no conflict check": run_arm("A2", lines, qs, model, ca, tmp, escalate_on_conflict=False),
        "A3 tools off": run_arm("A3", lines, qs, model, ca, tmp, tools=False),
        "A4 random drop": run_arm("A4", dropped, qs, model, ca, tmp),
        "A5 shuffled": run_arm("A5", shuffled, qs, model, ca, tmp),
    }
    S = {k: summarize(v) for k, v in arms.items()}
    print(f"VERITAS-COMPANION C006 | Loghub HDFS 2k | {platform.machine()} | Python {platform.python_version()}")
    print(f"{len(lines)} log lines, dedup keeps {len(ded)}; {eligible} blocks with >= 3 lines; {len(qs)} questions "
          f"(seed {SEED}); model: {model.model_id()}{'' if a.nim else ' (NOT A RESULT: model arms NOT RUN)'}")
    for k, s in S.items():
        acc = "  ".join(f"{kind} {c}/{n}" for kind, (c, n) in s["acc"].items())
        print(f"  {k:<22} statuses {s['statuses']}  ALLOW {s['allowed']} (wrong {s['false_allow']})  correct: {acc}")
    a1 = S["A1 companion"]
    v = {}
    v["P1"] = ("VACUOUS" if a1["allowed"] < 5 else ("HELD" if a1["false_allow"] == 0 else "FAILED"),
               f"A1 ALLOWed {a1['allowed']}, wrong {a1['false_allow']} (vacuity guard: fewer than 5 ALLOWed)")
    v["P2"] = ("HELD" if a1["supported"] < 0.30 * a1["n"] else "FAILED",
               f"tier-0 SUPPORTED {a1['supported']}/{a1['n']} (registered: < 30%)")
    if a.nim:
        def rate(s, kinds):
            c = sum(s["acc"][k][0] for k in kinds); n = sum(s["acc"][k][1] for k in kinds)
            return c / n
        drop_order = rate(S["A1 companion"], ["last", "first_component"]) - rate(S["A5 shuffled"], ["last", "first_component"])
        dcount = abs(rate(S["A1 companion"], ["count"]) - rate(S["A5 shuffled"], ["count"]))
        v["P3"] = ("HELD" if drop_order >= 0.25 and dcount <= 0.05 else "FAILED",
                   f"order accuracy fell {drop_order:+.3f} (need >= 0.25), count changed {dcount:.3f} (need <= 0.05)")
        v["P4"] = ("NOT RUN", "A0 (model alone on the full log) is run separately on the phone")
    else:
        v["P3"] = ("NOT EVALUABLE", "no arm answered any order question without a model")
        v["P4"] = ("NOT RUN", "needs a model")
    for k, (st, d) in v.items():
        print(f"{st:<13} {k}  {d}")
    if a.json:
        json.dump({"summary": S, "verdicts": v, "model": model.model_id()}, open(a.json, "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main()

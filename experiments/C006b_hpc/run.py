#!/usr/bin/env python3
"""C006b (registered in PREREG.md): the companion and the gate on Loghub HPC 2k.

  python experiments/C006b_hpc/fetch.py      # once; verifies the frozen hashes
  python experiments/C006b_hpc/run.py --sv ~/sovereign-veritas [--nim MODEL] [--json OUT] [--selftest]

Without --nim only the deterministic parts run (tier-0 tools, the gate, coverage); the model arms are
reported NOT RUN. --selftest checks the scorer and the shuffle control with an oracle that reads the log
it is given (anti-vacuity: the instrument must be able to fail). The arms see only question text and log
lines, never the truth.
"""
import argparse, csv, hashlib, importlib.util, json, os, platform, re, sys, tempfile
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, ROOT)
from companion import Companion  # noqa: E402
from companion.runtime import PROMPT  # noqa: E402
from companion.runtime_types import Result  # noqa: E402

DATA = os.path.join(ROOT, "data", "loghub_hpc")
SEED, N_KEYS = 6, 20
ORDER = ("last", "first")


class NoModel:
    """Stands in when no model is given: returns nothing. NOT A RESULT; model arms are NOT RUN."""
    def model_id(self):
        return "no-model"

    def count_tokens(self, text):
        return len(text.split())

    def complete(self, prompt):
        return "", 0, 0


class OracleReader:
    """Self-test only. Answers by reading the log in the prompt (so it is fooled by a shuffle, as a real
    reader would be). Not a model and never a result."""
    def model_id(self):
        return "oracle-reader-selftest"

    def count_tokens(self, text):
        return len(text.split())

    def complete(self, prompt):
        ctx, q = prompt.split("Question:", 1)
        lines = ctx.split("\n", 1)[1].split("\n\nAnswer with")[0].splitlines()
        node = re.search(r"node (\S+?) ?(?:\.|\?)$", q.split("\n")[0].strip()).group(1)
        mine = [ln for ln in lines if len(ln.split()) > 1 and ln.split()[1] == node]
        if q.strip().startswith("How many"):
            return str(len(mine)), 0, 0
        if not mine:
            return "", 0, 0
        return (mine[-1] if "last" in q else mine[0]), 0, 0


class ToolsOff(Companion):
    def cheap_answer(self, lines, question):
        return Result("ESCALATE")


def load(sv, name, rel):
    s = importlib.util.spec_from_file_location(name, os.path.join(sv, rel))
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def norm(s):
    return " ".join(str(s).split())


def questions(raw):
    rows = list(csv.DictReader(open(os.path.join(DATA, "HPC_2k.log_structured.csv"), encoding="utf-8")))
    by = defaultdict(list)
    for r in rows:
        by[r["Node"]].append(r)
    eligible = sorted(k for k, v in by.items() if len(v) >= 3)
    if len(eligible) < N_KEYS:
        print(f"COULD NOT RUN AS REGISTERED: {len(eligible)} nodes have >= 3 lines, need {N_KEYS}")
        sys.exit(3)
    pick = np.random.default_rng(SEED).choice(len(eligible), N_KEYS, replace=False)
    qs = []
    for i in sorted(pick):
        n = eligible[i]
        rs = sorted(by[n], key=lambda r: int(r["LineId"]))
        contents = Counter(norm(r["Content"]) for r in rs)
        for kind, r in (("last", rs[-1]), ("first", rs[0])):
            qs.append({"kind": kind, "q": f"Quote the {kind} line in this log that was logged by node {n}.",
                       "logid": r["LogId"], "content": norm(r["Content"]),
                       "content_unique": contents[norm(r["Content"])] == 1})
        qs.append({"kind": "count", "q": f"How many lines in this log were logged by node {n}?", "truth": str(len(rs))})
    return qs, len(eligible)


def correct(ans, q):
    a = norm(ans or "")
    if q["kind"] == "count":
        return re.search(rf"(?<![\d.]){q['truth']}(?![\d.])", a) is not None
    if re.search(rf"(?<!\d){re.escape(q['logid'])}(?!\d)", a):
        return True
    return q["content_unique"] and q["content"] in a


def run_arm(name, lines, qs, model, ca, tmp, kind="companion"):
    out = []
    if kind == "alone":
        for q in qs:
            text, _, _ = model.complete(PROMPT.format(context="\n".join(lines), question=q["q"]))
            out.append({"kind": q["kind"], "status": "MODEL", "decision": None, "ok": correct(text, q)})
        return out
    cls = ToolsOff if kind == "tools_off" else Companion
    comp = cls(model, escalate_on_conflict=(kind != "no_conflict"), log_path=os.path.join(tmp, f"{name}.jsonl"))
    for i, q in enumerate(qs):
        rec = comp.ask(f"{name}-{i}", q["q"], lines)
        r = {"status": rec.status, "delegated_to": rec.delegated_to, "final_result": rec.final_result,
             "cached_origin": rec.cached_origin}
        pkg = ca.package_for(r, f"{name}:{i}", "normal", os.path.join(tmp, "sandbox")) if ca else {"decision": {"decision": None}}
        out.append({"kind": q["kind"], "status": rec.status, "decision": pkg["decision"]["decision"],
                    "ok": correct(rec.final_result, q)})
    return out


def summarize(rows):
    allow = [r for r in rows if r["decision"] == "ALLOW"]
    acc = {k: (sum(r["ok"] for r in rows if r["kind"] == k), sum(1 for r in rows if r["kind"] == k))
           for k in ("last", "first", "count")}
    return {"n": len(rows), "supported": sum(r["status"] == "SUPPORTED" for r in rows), "allowed": len(allow),
            "false_allow": sum(not r["ok"] for r in allow), "statuses": dict(Counter(r["status"] for r in rows)),
            "acc": acc}


def rate(s, kinds):
    return sum(s["acc"][k][0] for k in kinds) / sum(s["acc"][k][1] for k in kinds)


def p3(a1, a5):
    drop = rate(a1, ORDER) - rate(a5, ORDER)
    dc = abs(rate(a1, ["count"]) - rate(a5, ["count"]))
    return ("HELD" if drop >= 0.25 and dc <= 0.05 else "FAILED",
            f"order accuracy fell {drop:+.3f} (need >= 0.25), count changed {dc:.3f} (need <= 0.05)")


def arms(lines, qs, model, ca, tmp):
    rng = np.random.default_rng(SEED)
    shuffled = [lines[i] for i in rng.permutation(len(lines))]
    ded = Companion.dedup(lines)
    drop = sorted(np.random.default_rng(SEED + 1).choice(len(lines), len(ded), replace=False))
    return {
        "A0 model alone": run_arm("A0", lines, qs, model, ca, tmp, "alone"),
        "A1 companion": run_arm("A1", lines, qs, model, ca, tmp),
        "A2 no conflict check": run_arm("A2", lines, qs, model, ca, tmp, "no_conflict"),
        "A3 tools off": run_arm("A3", lines, qs, model, ca, tmp, "tools_off"),
        "A4 random drop": run_arm("A4", [lines[i] for i in drop], qs, model, ca, tmp),
        "A5 shuffled": run_arm("A5", shuffled, qs, model, ca, tmp),
    }, len(ded)


def selftest(lines, qs):
    """The scorer must reward a correct reader, punish a wrong one, and the shuffle must hurt order questions."""
    tmp = tempfile.mkdtemp(prefix="c006b_st_")
    S = {k: summarize(v) for k, v in arms(lines, qs, OracleReader(), None, tmp)[0].items()}
    wrong = sum(correct("", q) for q in qs)
    a1 = S["A1 companion"]
    ok_reader = rate(a1, ORDER) == 1.0 and rate(a1, ["count"]) == 1.0
    verdict = p3(a1, S["A5 shuffled"])
    print(f"self-test: oracle reader A1 order {rate(a1, ORDER):.3f} count {rate(a1, ['count']):.3f}; "
          f"empty answers scored correct {wrong}/{len(qs)}; A5 order {rate(S['A5 shuffled'], ORDER):.3f}; P3 on oracle {verdict[0]}")
    ok = ok_reader and wrong == 0 and verdict[0] == "HELD"
    print(f"self-test {'PASS' if ok else 'FAIL'}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sv", required=True)
    ap.add_argument("--nim", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    fetch = load(HERE, "c006b_fetch", "fetch.py")
    for name, want in fetch.FROZEN.items():
        path = os.path.join(DATA, name)
        if not os.path.exists(path) or hashlib.sha256(open(path, "rb").read()).hexdigest() != want:
            print(f"COULD NOT RUN: {name} missing or not the frozen file; run fetch.py first")
            sys.exit(2)
    lines = open(os.path.join(DATA, "HPC_2k.log"), encoding="utf-8").read().splitlines()
    qs, eligible = questions(lines)
    if a.selftest:
        sys.exit(0 if selftest(lines, qs) else 1)
    ca = load(os.path.expanduser(a.sv), "sv_companion_action", "tools/companion_action.py")
    if a.nim:
        from companion.llm import NimModel
        model = NimModel(a.nim)
    else:
        model = NoModel()
    tmp = tempfile.mkdtemp(prefix="c006b_")
    A, nded = arms(lines, qs, model, ca, tmp)
    S = {k: summarize(v) for k, v in A.items()}
    print(f"VERITAS-COMPANION C006b | Loghub HPC 2k | {platform.machine()} | Python {platform.python_version()}")
    print(f"{len(lines)} log lines, dedup keeps {nded}; {eligible} nodes with >= 3 lines; {len(qs)} questions "
          f"(seed {SEED}); model: {model.model_id()}{'' if a.nim else ' (NOT A RESULT: model answers NOT RUN)'}")
    for k, s in S.items():
        acc = "  ".join(f"{kind} {c}/{n}" for kind, (c, n) in s["acc"].items())
        print(f"  {k:<22} statuses {s['statuses']}  ALLOW {s['allowed']} (wrong {s['false_allow']})  correct: {acc}")
    a1 = S["A1 companion"]
    v = {"P1": ("VACUOUS" if a1["allowed"] < 5 else ("HELD" if a1["false_allow"] == 0 else "FAILED"),
                f"A1 ALLOWed {a1['allowed']}, wrong {a1['false_allow']} (vacuity guard: fewer than 5 ALLOWed)"),
         "P2": ("HELD" if a1["supported"] < 0.30 * a1["n"] else "FAILED",
                f"tier-0 SUPPORTED {a1['supported']}/{a1['n']} (registered: < 30%)")}
    if a.nim:
        v["P3"] = p3(a1, S["A5 shuffled"])
        diff = rate(a1, ["last", "first", "count"]) - rate(S["A0 model alone"], ["last", "first", "count"])
        v["P4"] = ("HELD" if diff >= -1 / 60 else "FAILED", f"A1 minus A0 accuracy {diff:+.3f} (need >= -0.017)")
    else:
        v["P3"] = ("NOT RUN", "needs a model")
        v["P4"] = ("NOT RUN", "needs a model")
    for k, (st, d) in v.items():
        print(f"{st:<9} {k}  {d}")
    if a.json:
        json.dump({"summary": S, "verdicts": v, "model": model.model_id()}, open(a.json, "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main()

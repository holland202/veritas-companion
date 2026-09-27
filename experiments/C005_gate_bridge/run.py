#!/usr/bin/env python3
"""C005 - the companion's answers through the sovereign-veritas gate (registered as CA7 in
sovereign-veritas docs/COMPANION_ACTION.md, before this runner was written).

  python experiments/C005_gate_bridge/run.py --sv ~/sovereign-veritas [--seeds 1-20] [--json OUT]

For each C003 task: the companion answers every question twice (the second pass is served from the
cache), logging each delegation to JSONL. Escalated questions go to OracleModel, a test double whose
output is NOT A RESULT. Every log line becomes a sovereign-veritas package (tools/companion_action.py),
verified by tools/verify_package.py, and every ALLOWed answer is checked against the task's truth.
Exit: 0 CA7 held | 1 it failed | 2 could not run
"""
import argparse, importlib.util, json, os, platform, sys, tempfile
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "C003_routing_ladder"))
from companion import Companion  # noqa: E402
from companion.llm import NimModel, OracleModel  # noqa: E402
from task import make_task  # noqa: E402

spec = importlib.util.spec_from_file_location("c003_run", os.path.join(HERE, "..", "C003_routing_ladder", "run.py"))
c003 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c003)


def load(sv, name, rel):
    s = importlib.util.spec_from_file_location(name, os.path.join(sv, rel))
    if s is None or not os.path.isfile(os.path.join(sv, rel)):
        print(f"COULD NOT RUN: {rel} not found under {sv}")
        sys.exit(2)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sv", required=True, help="a sovereign-veritas checkout")
    ap.add_argument("--seeds", default="1-20")
    ap.add_argument("--json", default=None)
    ap.add_argument("--nim", default=None, metavar="MODEL",
                    help="a real NVIDIA-hosted model on the escalated path instead of the test double")
    a = ap.parse_args()
    sv = os.path.expanduser(a.sv)
    ca = load(sv, "sv_companion_action", "tools/companion_action.py")
    vp = load(sv, "sv_verify_package", "tools/verify_package.py")
    lo, hi = (int(x) for x in a.seeds.split("-"))
    tmp = tempfile.mkdtemp(prefix="c005_")
    tally, false_allow, not_consistent, bad_defer, deferred_model = Counter(), [], [], [], Counter()
    for seed in range(lo, hi + 1):
        lines, _, qs = make_task(seed)
        log = os.path.join(tmp, f"seed{seed}.jsonl")
        comp = Companion(NimModel(a.nim) if a.nim else OracleModel(), log_path=log)
        asked = []
        for rnd in (1, 2):
            for i, q in enumerate(qs):
                comp.ask(f"s{seed}q{i}r{rnd}", q["q"], lines)
                asked.append(q)
        recs = [json.loads(x) for x in open(log, encoding="utf-8")]
        assert len(recs) == len(asked)
        for n, (rec, q) in enumerate(zip(recs, asked), 1):
            pkg = ca.package_for(rec, f"seed{seed}:{n}", "normal", os.path.join(tmp, "sandbox"))
            dec = pkg["decision"]["decision"]
            origin = rec.get("cached_origin")
            tally[(rec["status"], origin, dec)] += 1
            if any(not ok for _, ok, _ in vp.verify(pkg)):
                not_consistent.append((seed, n))
            if dec == "ALLOW" and not c003.correct(rec["final_result"], q["truth"]):
                false_allow.append((seed, n, q["q"], rec["final_result"], q["truth"]))
            if dec == "DEFER" and rec["delegated_to"] == "large_model":
                deferred_model[bool(c003.correct(rec["final_result"], q["truth"]))] += 1
            must_defer = rec["status"] in ("UNCERTAIN", "ESCALATE") or (rec["status"] == "CACHED" and origin != "deterministic")
            if must_defer and dec != "DEFER":
                bad_defer.append((seed, n, rec["status"], origin, dec))
    total = sum(tally.values())
    allows = sum(v for k, v in tally.items() if k[2] == "ALLOW")
    print(f"VERITAS-COMPANION C005 (CA7) | seeds {lo}-{hi} | {platform.machine()} | Python {platform.python_version()}")
    print(f"{total} delegation records -> {total} packages")
    for (st, origin, dec), v in sorted(tally.items(), key=lambda kv: (kv[0][0], str(kv[0][1]), kv[0][2])):
        print(f"  {st:<10} origin {str(origin):<13} {dec:<6} {v}")
    print(f"deferred large-model answers that were in fact right: {deferred_model[True]} of "
          f"{deferred_model[True] + deferred_model[False]} (what deferring costs; the model is "
          f"{'NVIDIA-hosted ' + a.nim if a.nim else 'the test double, NOT A RESULT'})")
    verdicts = {
        "CA7a": (allows > 0 and not false_allow, f"{allows} ALLOWed answers, {len(false_allow)} wrong against the truth"),
        "CA7b": (not bad_defer, f"{len(bad_defer)} conflict/escalation/model-cache records not DEFERred"),
        "CA7c": (not not_consistent, f"{total - len(not_consistent)}/{total} packages verify CONSISTENT"),
    }
    for k, (ok, d) in verdicts.items():
        print(f"{'HELD  ' if ok else 'FAILED'} {k}  {d}")
    for x in false_allow[:5] + bad_defer[:5]:
        print("  example:", x)
    held = sum(ok for ok, _ in verdicts.values())
    print(f"VERDICT  {held} of 3 held")
    if a.json:
        json.dump({"tally": {"|".join(map(str, k)): v for k, v in tally.items()},
                   "verdicts": {k: {"held": ok, "detail": d} for k, (ok, d) in verdicts.items()}},
                  open(a.json, "w"), indent=1, sort_keys=True)
    sys.exit(0 if held == 3 else 1)


if __name__ == "__main__":
    main()

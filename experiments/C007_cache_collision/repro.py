#!/usr/bin/env python3
"""C007: cache and dedup collisions from lossy normalisation (found 2026-09-27 by cache_attack.py on the S25).

The companion keyed its cache, and deduplicated lines, on text that was case-folded and had its whitespace
collapsed. Three consequences, each checked here against the sovereign-veritas companion check (the rule the
gate applies: CACHED with cached_origin "deterministic" is PASS, so ALLOW):

  R1 a case-sensitive value (an id, a hash) served from the cache for a log that says something else;
  R2 a deterministic answer served for a log in which the tool finds nothing at all;
  R3 dedup silently drops a conflicting line, so a conflict reads as SUPPORTED.

  python experiments/C007_cache_collision/repro.py --sv ~/sovereign-veritas
Exit 0 if no case gives a wrong answer that the check would PASS; 1 otherwise.
"""
import argparse, importlib.util, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from companion import Companion  # noqa: E402


class Counting:
    calls = 0
    def model_id(self): return "counting-null"
    def count_tokens(self, t): return len(t.split())
    def complete(self, p):
        Counting.calls += 1
        return "", 0, 0


def check(sv):
    s = importlib.util.spec_from_file_location("sv_verify", os.path.join(sv, "tools", "verify_package.py"))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m.companion_check


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--sv", required=True); a = ap.parse_args()
    cc = check(os.path.expanduser(a.sv))
    cases = [  # (name, question, first log, second log, the literal right answer for the second log or None)
        ("R1 case-sensitive value", "What is the value of token?", ["token = Ab12"], ["token = aB12"], "aB12"),
        ("R1 NaN vs nan (the S25 case)", "What is the temperature of P1?", ["P1 temperature NaN"], ["P1 temperature nan"], "nan"),
        ("R2 no match, still answered", "What is the temperature of P1?", ["P1 temperature NaN"], ["P1  temperature  nan"], None),
    ]
    bad = 0
    for name, q, l1, l2, right in cases:
        c = Companion(Counting())
        c.ask("a", q, l1)
        r = c.ask("b", q, l2)
        rec = {"status": r.status, "delegated_to": r.delegated_to, "final_result": r.final_result, "cached_origin": r.cached_origin}
        verdict = cc(rec)["verdict"]
        wrong = (right is None and r.status in ("SUPPORTED", "CACHED")) or (right is not None and r.final_result != right)
        released_wrong = wrong and verdict == "PASS"
        bad += released_wrong
        print(f"{name:<30} second log {l2!r}: status {r.status}, answer {r.final_result!r}, right {right!r}, "
              f"check {verdict}{'  <- WRONG ANSWER RELEASED' if released_wrong else ''}")
    c = Companion(Counting())
    r = c.ask("c", "What is the value of token?", ["token = Ab12", "token = aB12"])
    rec = {"status": r.status, "delegated_to": r.delegated_to, "final_result": r.final_result, "cached_origin": r.cached_origin}
    verdict = cc(rec)["verdict"]
    released = r.status == "SUPPORTED" and verdict == "PASS"
    bad += released
    print(f"{'R3 dedup hides a conflict':<30} log ['token = Ab12', 'token = aB12']: status {r.status}, answer {r.final_result!r}, "
          f"right: a conflict (UNCERTAIN), check {verdict}{'  <- WRONG ANSWER RELEASED' if released else ''}")
    print(f"model calls {Counting.calls}; wrong answers the check would PASS: {bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

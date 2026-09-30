#!/usr/bin/env python3
"""The 30-second demo: what the companion answers itself, what it flags, what it passes up.

  python scripts/demo_30s.py

No model and no network: the large model is OracleModel, a rule-following test double that reads the
context it is sent, so its token counts are words, NOT a real model's tokens. The routing, statuses,
evidence lines, cache and context digests are the real code. Exit 0 only if every line comes out as
expected.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from companion import Companion  # noqa: E402
from companion.llm import OracleModel  # noqa: E402

LOG = ["P01 pressure 40", "P02 status RUNNING", "P01 pressure 40", "P02 pressure 31",
       "UPDATE P02 pressure 30", "P02 temperature 64", "P03 temperature 71", "P03 status RUNNING"]


class Counting(OracleModel):
    calls = words = 0

    def complete(self, prompt):
        Counting.calls += 1
        text, pt, ct = super().complete(prompt)
        Counting.words += pt
        return text, pt, ct


def main():
    c = Companion(Counting())
    cases = [
        ("What is the pressure of P01?", "SUPPORTED"),     # stated once (twice, identical): the tool answers
        ("What is the pressure of P02?", "UNCERTAIN"),     # 31 then 30: a conflict is flagged, not guessed
        ("Which asset has the highest temperature?", "ESCALATE"),  # outside the tools: the model is asked
        ("What is the pressure of P01?", "CACHED"),        # same question, same exact lines: no work at all
    ]
    ok = True
    for q, want in cases:
        r = c.ask("demo", q, LOG)
        good = r.status == want
        ok &= good
        print(f"{'ok ' if good else 'BAD'} {q:<42} {r.status:<9} -> {r.final_result!r:<8} via {r.delegated_to:<13}"
              f" ctx {r.context_sha256[:12]}")
    r = c.ask("demo", "What is the pressure of P01?", LOG + ["P01 pressure 41"])
    good = r.status == "UNCERTAIN"
    ok &= good
    print(f"{'ok ' if good else 'BAD'} {'same question, one changed line':<42} {r.status:<9} -> {r.final_result!r:<8}"
          f" (not served stale from the cache: C007)")
    print(f"    model calls {Counting.calls} of {len(cases) + 1} questions (a model-only setup makes {len(cases) + 1})")
    print("DEMO", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

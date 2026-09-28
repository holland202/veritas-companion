# C007: cache and dedup collisions: wrong answers the gate would ALLOW. Found, reproduced, fixed

## What broke

The companion keyed its answer cache and its line dedup on **normalised** text (case-folded, whitespace
collapsed). The code comment said this was "nothing semantic". It was semantic. The sovereign-veritas check
gives **PASS** to a CACHED answer of deterministic origin, and PASS means ALLOW. So every collision below is a
wrong answer that the gate would release:

```
R1 case-sensitive value        second log ['token = aB12']: status CACHED, answer 'Ab12', right 'aB12', check PASS  <- WRONG ANSWER RELEASED
R1 NaN vs nan (the S25 case)   second log ['P1 temperature nan']: status CACHED, answer 'NaN', right 'nan', check PASS  <- WRONG ANSWER RELEASED
R2 no match, still answered    second log ['P1  temperature  nan']: status CACHED, answer 'NaN', right None, check PASS  <- WRONG ANSWER RELEASED
R3 dedup hides a conflict      log ['token = Ab12', 'token = aB12']: status SUPPORTED, answer 'Ab12', right: a conflict (UNCERTAIN), check PASS  <- WRONG ANSWER RELEASED
model calls 0; wrong answers the check would PASS: 4
```
(`output_before_fix_x86_64.txt`, from `repro.py` on the code before the fix)

- **R1:** a case-sensitive value (an id, a hash) is served from the cache for a log that says something else.
  `NaN`/`nan` is the weakest case, since both parse as the same float; `Ab12`/`aB12` has no such excuse.
- **R2 is the worst one:** the tool finds *nothing* in the second log (the double spaces don't match its
  pattern), yet it gets a cached "deterministic" answer with zero model calls.
- **R3:** dedup drops `token = aB12` as a duplicate of `token = Ab12`, so a real conflict reads as SUPPORTED.

**Found by** `cache_attack.py`, a red-team script run on the S25 on 2026-09-27: 450 cases, 20 "true cache
candidates", all variants of `P1 temperature NaN` vs `nan` with changed spacing, every one with `calls: 0`
and `cached_origin: deterministic`. `repro.py` turns that into the four cases above and adds R1 and R3, which
the script did not try.

## Fix

- `fingerprint()` is SHA-256 over the **exact** text of the question and the lines. Each part is
  length-prefixed, so shifting a boundary (`"ab","c"` vs `"a","bc"`) also changes the key.
- `dedup()` removes **exact** duplicate lines only.
- `normalize()` is kept for display and analysis, and nothing that decides an answer uses it.

After the fix (`output_after_fix_x86_64.txt`):

```
R1 case-sensitive value        second log ['token = aB12']: status SUPPORTED, answer 'aB12', right 'aB12', check PASS
R1 NaN vs nan (the S25 case)   second log ['P1 temperature nan']: status SUPPORTED, answer 'nan', right 'nan', check PASS
R2 no match, still answered    second log ['P1  temperature  nan']: status ESCALATE, answer '', right None, check INSUFFICIENT_EVIDENCE
R3 dedup hides a conflict      log ['token = Ab12', 'token = aB12']: status UNCERTAIN, answer '', right: a conflict (UNCERTAIN), check INSUFFICIENT_EVIDENCE
model calls 2; wrong answers the check would PASS: 0
```

## Confirmed on the S25 after the fix (2026-09-27, aarch64, after `git pull` to c4d7f62), verbatim

```
======================================================================
FINAL
cases: 450
true cache candidates: 0
exceptions (expected escalations): 162
======================================================================
NO TRUE CACHE-POISONING / FINGERPRINT COLLISION FOUND.
```

Before the fix, the same script found 20 candidates and 150 escalations. The 12 extra escalations fit the
fix: inputs that used to get a cached answer now go to the model.

The script is not in this repository, so this confirms the fix on the device only. `repro.py` is the
check that anyone can re-run.

## Tests

- `test_fingerprint_normalises_only_case_and_space` **asserted the collision** that this attack exploited.
  It is replaced by `test_fingerprint_is_exact`; the old name is recorded in the new test's comment.
- `test_c007_no_wrong_answer_from_cache_or_dedup` pins R1, R2 and R3.
- Both new tests fail on the old code (2 failed) and pass on the new (suite: 9 passed).
- `test_dedup_keeps_first_and_order` now expects `p01  pressure 40` to be kept, because it differs from
  `P01 pressure 40` in case and spacing.

## Effect on earlier results

On x86_64, before and after the fix, the deterministic outputs of C001 (`--seed 101 --oracle`), C003
(`--seed 101 --oracle`), C005 and C006b are identical. C005 differs only in stderr progress lines. No
recorded number changes.

The C006b S25 model run used the old code. It was not affected: its 60 questions are distinct strings, so no
two of them collided, and dedup kept 1,999 lines under both rules.

## Limits and what is still open

- **Exact keys give up some cache hits,** for example a log re-sent with different spacing. That cost is not
  measured yet.
- **The deeper issue stays open:** the gate trusts `cached_origin` as a label. It is the same class of break
  as issue #4's B1 in sovereign-veritas, where status is an unauthenticated label. A cache entry should carry
  the digest of the exact context it was computed from, and the check should recompute it. This is
  registered here as unrun.

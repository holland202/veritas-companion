"""The companion runtime: cheap tiers first, escalation with evidence, every delegation logged."""
from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field

from .fingerprint import fingerprint
from .kv import norm_key, parse_kv
from .runtime_types import Result  # noqa: F401  (re-exported)

PROMPT = ("Context:\n{context}\n\nAnswer with the value only. If a value was updated, give the latest value.\n"
          "Question: {question}\nAnswer:")


@dataclass
class Delegation:
    task_id: str
    task_type: str
    delegated_to: str
    companion_seconds: float
    large_prompt_tokens: int
    large_completion_tokens: int
    companion_result: str
    status: str
    escalated: bool
    final_result: str
    cached_origin: str | None = None  # for a CACHED answer: the tier that produced it ("deterministic" or "large_model")
    # fingerprint() of the exact question and context lines the answer was computed from (C007). A consumer
    # holding the lines can recompute it; a cached answer carries the key of the context it was looked up for.
    context_sha256: str | None = None


class Companion:
    LOOKUP = re.compile(r"^What is the (pressure|temperature|status) of (P\d+)\?$")
    KV_LOOKUP = re.compile(r"^What is the value of (.+)\?$")

    def __init__(self, model, escalate_on_conflict=True, dedup=True, log_path=None):
        self.model, self.escalate_on_conflict, self.dedup_on = model, escalate_on_conflict, dedup
        self.cache, self.log, self.log_path = {}, [], log_path

    # tier 0: deterministic tools -------------------------------------------------------------------------
    @staticmethod
    def dedup(lines):
        # Exact lines only. Normalised dedup dropped "token = aB12" after "token = Ab12" and hid the conflict (C007).
        seen, kept = set(), []
        for ln in lines:
            k = ln
            if k not in seen:
                seen.add(k)
                kept.append(ln)
        return kept

    @staticmethod
    def extract(lines, asset, fld):
        """All values stated for (asset, field), in order, with the lines that state them."""
        pat = re.compile(rf"^(?:t=\d+ )?(?:UPDATE )?{re.escape(asset)} {fld} (\S+)$")
        return [(m.group(1), ln) for ln in lines if (m := pat.match(ln.strip()))]

    @staticmethod
    def extract_kv(lines, key):
        want = norm_key(key)
        return [(kv[1], ln) for ln in lines if (kv := parse_kv(ln)) and kv[0] == want]

    def cheap_answer(self, lines, question):
        m = self.LOOKUP.match(question.strip())
        k = self.KV_LOOKUP.match(question.strip())
        if m:
            fld, asset = m.groups()
            found = self.extract(lines, asset, fld)
        elif k:
            found = self.extract_kv(lines, k.group(1))
        else:
            from .tools import TOOLS
            for tool in TOOLS:
                r = tool(lines, question.strip())
                if r is not None:
                    return r
            return Result("ESCALATE")
        values = list(dict.fromkeys(v for v, _ in found))
        if len(values) == 1:
            return Result("SUPPORTED", values[0], [ln for _, ln in found][:3])
        if len(values) > 1 and not self.escalate_on_conflict:  # null arm: answers anyway, first value seen
            return Result("SUPPORTED", values[0], [ln for _, ln in found][:3])
        return Result("UNCERTAIN" if values else "ESCALATE", None, [ln for _, ln in found][:3])

    # the pipeline ----------------------------------------------------------------------------------------
    def ask(self, task_id, question, lines):
        t0 = time.perf_counter()
        ctx = self.dedup(lines) if self.dedup_on else list(lines)
        key = fingerprint(question, *ctx)
        self._key = key
        if key in self.cache:
            # A cached answer keeps the provenance of the tier that produced it. Found 2026-09-27 while
            # wiring the companion to the sovereign-veritas gate: CACHED alone could not say whether a
            # deterministic tool or the large model had answered, so a consumer could not tell which to trust.
            value, origin = self.cache[key]
            return self._record(task_id, question, t0, "cache", 0, 0, Result("CACHED", value), value,
                                cached_origin=origin)
        r = self.cheap_answer(ctx, question)
        if r.status == "SUPPORTED":
            self.cache[key] = (r.value, "deterministic")
            return self._record(task_id, question, t0, "deterministic", 0, 0, r, r.value)
        t_cheap = time.perf_counter() - t0
        text, pt, ct = self.model.complete(PROMPT.format(context="\n".join(ctx), question=question))
        self.cache[key] = (text, "large_model")
        # companion_seconds is the cheap tiers' time only, set before the log line is written (it used to be
        # set after, so the JSONL line held the total including the model call while the object held t_cheap).
        return self._record(task_id, question, t0, "large_model", pt, ct, r, text, seconds=t_cheap)

    def _record(self, task_id, question, t0, to, pt, ct, r, final, cached_origin=None, seconds=None):
        rec = Delegation(task_id, "lookup" if (self.LOOKUP.match(question) or self.KV_LOOKUP.match(question)) else "open", to,
                         time.perf_counter() - t0 if seconds is None else seconds, pt, ct, str(r.value), r.status,
                         to == "large_model", str(final), cached_origin, getattr(self, "_key", None))
        self.log.append(rec)
        if self.log_path:
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(asdict(rec), sort_keys=True) + "\n")
        return rec

"""The companion runtime: cheap tiers first, escalation with evidence, every delegation logged."""
from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field

from .fingerprint import fingerprint, normalize
from .kv import norm_key, parse_kv

PROMPT = ("Context:\n{context}\n\nAnswer with the value only. If a value was updated, give the latest value.\n"
          "Question: {question}\nAnswer:")


@dataclass
class Result:
    """What the companion hands back. status: SUPPORTED (answered with evidence), UNCERTAIN (cheap tier saw
    conflicting evidence), ESCALATE (outside the cheap tiers), CACHED (seen before)."""
    status: str
    value: str | None = None
    evidence: list = field(default_factory=list)


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


class Companion:
    LOOKUP = re.compile(r"^What is the (pressure|temperature|status) of (P\d+)\?$")
    KV_LOOKUP = re.compile(r"^What is the value of (.+)\?$")

    def __init__(self, model, escalate_on_conflict=True, dedup=True, log_path=None):
        self.model, self.escalate_on_conflict, self.dedup_on = model, escalate_on_conflict, dedup
        self.cache, self.log, self.log_path = {}, [], log_path

    # tier 0: deterministic tools -------------------------------------------------------------------------
    @staticmethod
    def dedup(lines):
        seen, kept = set(), []
        for ln in lines:
            k = normalize(ln)
            if k not in seen:
                seen.add(k)
                kept.append(ln)
        return kept

    @staticmethod
    def extract(lines, asset, fld):
        """All values stated for (asset, field), in order, with the lines that state them."""
        pat = re.compile(rf"^(?:UPDATE )?{re.escape(asset)} {fld} (\S+)")
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
        if key in self.cache:
            return self._record(task_id, question, t0, "cache", 0, 0, Result("CACHED", self.cache[key]),
                                self.cache[key])
        r = self.cheap_answer(ctx, question)
        if r.status == "SUPPORTED":
            self.cache[key] = r.value
            return self._record(task_id, question, t0, "deterministic", 0, 0, r, r.value)
        t_cheap = time.perf_counter() - t0
        text, pt, ct = self.model.complete(PROMPT.format(context="\n".join(ctx), question=question))
        self.cache[key] = text
        rec = self._record(task_id, question, t0, "large_model", pt, ct, r, text)
        rec.companion_seconds = t_cheap
        return rec

    def _record(self, task_id, question, t0, to, pt, ct, r, final):
        rec = Delegation(task_id, "lookup" if (self.LOOKUP.match(question) or self.KV_LOOKUP.match(question)) else "open", to,
                         time.perf_counter() - t0, pt, ct, str(r.value), r.status, to == "large_model", str(final))
        self.log.append(rec)
        if self.log_path:
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(asdict(rec), sort_keys=True) + "\n")
        return rec

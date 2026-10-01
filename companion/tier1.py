"""Tier-1: small local model contract for the adaptive cascade (C008).

Tier 1 is NOT an authority. It may only return a structured result. SUPPORTED
requires evidence; anything else (or malformed output) escalates. Numerical
confidence scores are never treated as proof.

No trained ~135M model is shipped with this repository (README: designed only,
NOT TRAINED, not wired). The default backend is therefore a fail-closed stub
that always escalates. A real backend can be supplied later without changing
the routing policy.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any


VALID_STATUS = frozenset({"SUPPORTED", "UNCERTAIN", "ESCALATE"})


@dataclass
class Tier1Result:
    """Structured Tier-1 output. Fail-closed on any missing/malformed field."""
    answer: str | None = None
    status: str = "ESCALATE"
    evidence: list = field(default_factory=list)
    reason: str = ""
    should_escalate: bool = True
    raw: str | None = None  # original model text, for logging

    def is_valid(self) -> bool:
        if self.status not in VALID_STATUS:
            return False
        if self.status == "SUPPORTED":
            if not self.answer or not isinstance(self.evidence, list) or len(self.evidence) == 0:
                return False
            if self.should_escalate:
                return False  # SUPPORTED must not request escalation
        if self.status in ("UNCERTAIN", "ESCALATE") and not self.should_escalate:
            return False
        return True


def parse_tier1_output(text: str) -> Tier1Result:
    """Parse model text into Tier1Result. Any failure → ESCALATE (fail-closed)."""
    if not text or not text.strip():
        return Tier1Result(status="ESCALATE", reason="empty_output", should_escalate=True, raw=text)

    # Prefer a JSON object anywhere in the response.
    blob = None
    m = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if m:
        try:
            blob = json.loads(m.group(0))
        except json.JSONDecodeError:
            blob = None
    if blob is None:
        # Try whole text
        try:
            blob = json.loads(text.strip())
        except json.JSONDecodeError:
            return Tier1Result(status="ESCALATE", reason="unparseable", should_escalate=True, raw=text)

    if not isinstance(blob, dict):
        return Tier1Result(status="ESCALATE", reason="not_object", should_escalate=True, raw=text)

    status = str(blob.get("status", "ESCALATE")).upper().strip()
    if status not in VALID_STATUS:
        status = "ESCALATE"

    evidence = blob.get("evidence", [])
    if not isinstance(evidence, list):
        evidence = []
    evidence = [str(e) for e in evidence if e is not None]

    answer = blob.get("answer")
    if answer is not None:
        answer = str(answer).strip() or None

    reason = str(blob.get("reason", "") or "")
    # Explicit should_escalate wins; otherwise derive from status.
    if "should_escalate" in blob:
        should = bool(blob["should_escalate"])
    else:
        should = status != "SUPPORTED"

    r = Tier1Result(
        answer=answer,
        status=status,
        evidence=evidence,
        reason=reason,
        should_escalate=should,
        raw=text,
    )
    if not r.is_valid():
        return Tier1Result(
            status="ESCALATE",
            reason=f"invalid_after_parse:{status}",
            should_escalate=True,
            raw=text,
        )
    return r


class Tier1Backend:
    """Interface. complete(prompt) -> (text, prompt_tokens, completion_tokens)."""

    def complete(self, prompt: str) -> tuple[str, int, int]:
        raise NotImplementedError

    def model_id(self) -> str:
        return "tier1-unknown"


class AlwaysEscalateTier1(Tier1Backend):
    """Default when no small model is available. Always produces a valid ESCALATE."""

    def model_id(self) -> str:
        return "tier1-always-escalate-stub"

    def complete(self, prompt: str) -> tuple[str, int, int]:
        payload = json.dumps({
            "answer": None,
            "status": "ESCALATE",
            "evidence": [],
            "reason": "no_small_model_wired",
            "should_escalate": True,
        })
        # Token estimate: whitespace words (same convention as OracleModel).
        pt = len(prompt.split())
        return payload, pt, 1


# Prompt that forces structured output. Keep short; Tier-1 is the cheap tier.
TIER1_PROMPT = (
    "Context:\n{context}\n\n"
    "Question: {question}\n\n"
    "Reply with a single JSON object only, no other text:\n"
    '{{"answer": "<value or null>", "status": "SUPPORTED|UNCERTAIN|ESCALATE", '
    '"evidence": ["<supporting line>", ...], "reason": "<short>", "should_escalate": true|false}}\n'
    "Rules: SUPPORTED requires non-empty evidence and should_escalate=false. "
    "If unsure or no clear evidence, use UNCERTAIN or ESCALATE with should_escalate=true.\n"
)


def evidence_in_context(evidence: list, lines: list[str]) -> bool:
    """Every evidence string must appear as a substring of some context line (exact text)."""
    if not evidence:
        return False
    joined = "\n".join(lines)
    return all(e in joined for e in evidence if e)


def run_tier1(backend: Tier1Backend, question: str, lines: list[str]) -> tuple[Tier1Result, int, int]:
    """Call Tier-1, parse, fail-closed. Returns (result, prompt_tokens, completion_tokens).

    After a valid SUPPORTED parse, evidence lines are checked against the context. Missing
    evidence forces ESCALATE (the important failure is accepting an unsupported answer).
    """
    prompt = TIER1_PROMPT.format(context="\n".join(lines), question=question)
    try:
        text, pt, ct = backend.complete(prompt)
    except Exception as e:  # noqa: BLE001 — any backend failure escalates
        return Tier1Result(status="ESCALATE", reason=f"backend_error:{type(e).__name__}",
                           should_escalate=True), 0, 0
    r = parse_tier1_output(text)
    if r.status == "SUPPORTED" and r.is_valid():
        if not evidence_in_context(r.evidence, lines):
            return Tier1Result(
                status="ESCALATE",
                reason="evidence_not_in_context",
                should_escalate=True,
                raw=text,
            ), pt, ct
    return r, pt, ct

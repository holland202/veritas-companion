"""Shared result type."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Result:
    """What the companion hands back. status: SUPPORTED (answered with evidence), UNCERTAIN (cheap tier saw
    conflicting evidence), ESCALATE (outside the cheap tiers), CACHED (seen before)."""
    status: str
    value: str | None = None
    evidence: list = field(default_factory=list)

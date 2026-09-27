"""veritas-companion: a cheap efficiency layer beside a large model. Deterministic tools first, a small model
second, the large model only when cheaper methods cannot answer with evidence. The companion proposes; it is
never the authority. Every delegation is logged so its usefulness is measured, not felt."""
from .fingerprint import fingerprint, normalize
from .runtime import Companion, Result

__version__ = "0.1.0"
__all__ = ["Companion", "Result", "fingerprint", "normalize"]

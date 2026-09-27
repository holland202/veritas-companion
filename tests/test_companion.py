import os
import sys

from companion import Companion, fingerprint
from companion.llm import OracleModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "experiments", "C001_context_economy"))
from task import make_task  # noqa: E402

LINES = ["P01 pressure 40", "P01 pressure 40", "p01  pressure 40", "P02 status RUNNING", "UPDATE P02 pressure 30",
         "P02 pressure 25"]


def test_fingerprint_normalises_only_case_and_space():
    assert fingerprint("P01 pressure 40") == fingerprint(" p01   PRESSURE 40 ")
    assert fingerprint("P01 pressure 40") != fingerprint("P01 pressure 41")


def test_dedup_keeps_first_and_order():
    assert Companion.dedup(LINES) == ["P01 pressure 40", "P02 status RUNNING", "UPDATE P02 pressure 30",
                                      "P02 pressure 25"]


def test_conflict_is_uncertain_not_answered():
    c = Companion(OracleModel())
    assert c.cheap_answer(LINES, "What is the pressure of P01?").status == "SUPPORTED"
    assert c.cheap_answer(LINES, "What is the pressure of P02?").status == "UNCERTAIN"
    assert c.cheap_answer(LINES, "Which RUNNING asset has the highest temperature?").status == "ESCALATE"


def test_null_arm_answers_conflicts_wrongly():
    c = Companion(OracleModel(), escalate_on_conflict=False)
    r = c.cheap_answer(LINES, "What is the pressure of P02?")
    assert r.status == "SUPPORTED" and r.value == "30"  # first seen, whatever it is: the guard is what prevents this


def test_cache_hits_on_repeat_and_logs_everything():
    c = Companion(OracleModel())
    first = c.ask("a", "Which RUNNING asset has the highest temperature?", LINES)
    again = c.ask("b", "Which RUNNING asset has the highest temperature?", LINES)
    assert first.delegated_to == "large_model" and again.delegated_to == "cache"
    assert again.large_prompt_tokens == 0 and len(c.log) == 2


def test_task_is_deterministic_and_has_ground_truth_for_every_ask():
    a, b = make_task(5), make_task(5)
    assert a == b
    lines, asks = a
    assert len(asks) == 30 and all(exp for _, exp, _ in asks)
    assert any(ln.startswith("UPDATE") for ln in lines)

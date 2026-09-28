import os
import sys

from companion import Companion, fingerprint
from companion.llm import OracleModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "experiments", "C001_context_economy"))
from task import make_task  # noqa: E402

LINES = ["P01 pressure 40", "P01 pressure 40", "p01  pressure 40", "P02 status RUNNING", "UPDATE P02 pressure 30",
         "P02 pressure 25"]


def test_fingerprint_is_exact():
    # Was test_fingerprint_normalises_only_case_and_space, which asserted the collision C007 exploited.
    assert fingerprint("P01 pressure 40") != fingerprint(" p01   PRESSURE 40 ")
    assert fingerprint("token = Ab12") != fingerprint("token = aB12")
    assert fingerprint("P01 pressure 40") != fingerprint("P01 pressure 41")
    assert fingerprint("ab", "c") != fingerprint("a", "bc")  # part boundaries count


def test_c007_no_wrong_answer_from_cache_or_dedup():
    class Null:
        def model_id(self): return "null"
        def count_tokens(self, t): return 0
        def complete(self, p): return "", 0, 0
    c = Companion(Null())
    c.ask("a", "What is the value of token?", ["token = Ab12"])
    assert c.ask("b", "What is the value of token?", ["token = aB12"]).final_result == "aB12"
    c.ask("c", "What is the temperature of P1?", ["P1 temperature NaN"])
    assert c.ask("d", "What is the temperature of P1?", ["P1  temperature  nan"]).status not in ("SUPPORTED", "CACHED")
    assert c.ask("e", "What is the value of token?", ["token = Ab12", "token = aB12"]).status == "UNCERTAIN"


def test_dedup_keeps_first_and_order():
    # Exact duplicates only since C007: "p01  pressure 40" differs in case and spacing, so it stays.
    assert Companion.dedup(LINES) == ["P01 pressure 40", "p01  pressure 40", "P02 status RUNNING",
                                      "UPDATE P02 pressure 30", "P02 pressure 25"]


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


def test_kv_reader_and_kv_lookup():
    from companion.kv import parse_kv
    assert parse_kv("llama_context: n_ctx         = 4096") == ("n_ctx", "4096")
    assert parse_kv("slot get_availabl: id  0 | task -1 | n_past = 2331") == ("n_past", "2331")
    assert parse_kv("srv  log_server_r: request: POST /completion 127.0.0.1 200") is None
    lines = ["a: n_ctx = 4096", "a: n_ctx = 4096", "b: n_past = 1", "b: n_past = 2"]
    c = Companion(OracleModel())
    assert c.cheap_answer(lines, "What is the value of n_ctx?").value == "4096"
    assert c.cheap_answer(lines, "What is the value of n_past?").status == "UNCERTAIN"


def test_cached_answer_keeps_its_origin(tmp_path):
    """A CACHED record says which tier produced the answer, in memory and in the JSONL log."""
    import json
    from companion import Companion
    from companion.llm import OracleModel
    log = tmp_path / "d.jsonl"
    c = Companion(OracleModel(), log_path=str(log))
    lines = ["P1 pressure 40", "P1 temperature 70"]
    c.ask("a", "What is the pressure of P1?", lines)          # deterministic
    c.ask("b", "Summarise the log.", lines)                   # large model
    r1 = c.ask("a2", "What is the pressure of P1?", lines)
    r2 = c.ask("b2", "Summarise the log.", lines)
    assert (r1.status, r1.cached_origin) == ("CACHED", "deterministic")
    assert (r2.status, r2.cached_origin) == ("CACHED", "large_model")
    rows = [json.loads(x) for x in log.read_text().splitlines()]
    assert [r["cached_origin"] for r in rows] == [None, None, "deterministic", "large_model"]

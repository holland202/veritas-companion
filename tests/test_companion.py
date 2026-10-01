import os
import sys

from companion import Companion, fingerprint
from companion.llm import OracleModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "experiments", "C001_context_economy"))
from task import make_task  # noqa: E402

LINES = ["P01 pressure 40", "P01 pressure 40", "p01  pressure 40", "P02 status RUNNING", "UPDATE P02 pressure 30",
         "P02 pressure 25"]


def test_fingerprint_is_exact():
    assert fingerprint("P01 pressure 40") != fingerprint(" p01   PRESSURE 40 ")
    assert fingerprint("token = Ab12") != fingerprint("token = aB12")
    assert fingerprint("P01 pressure 40") != fingerprint("P01 pressure 41")
    assert fingerprint("ab", "c") != fingerprint("a", "bc")


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
    assert r.status == "SUPPORTED" and r.value == "30"


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
    import json
    from companion import Companion
    from companion.llm import OracleModel
    log = tmp_path / "d.jsonl"
    c = Companion(OracleModel(), log_path=str(log))
    lines = ["P1 pressure 40", "P1 temperature 70"]
    c.ask("a", "What is the pressure of P1?", lines)
    c.ask("b", "Summarise the log.", lines)
    r1 = c.ask("a2", "What is the pressure of P1?", lines)
    r2 = c.ask("b2", "Summarise the log.", lines)
    assert (r1.status, r1.cached_origin) == ("CACHED", "deterministic")
    assert (r2.status, r2.cached_origin) == ("CACHED", "large_model")
    rows = [json.loads(x) for x in log.read_text().splitlines()]
    assert [r["cached_origin"] for r in rows] == [None, None, "deterministic", "large_model"]


def test_record_carries_exact_context_digest():
    from companion import fingerprint
    c = Companion(OracleModel())
    lines = ["P01 pressure 40"]
    r1 = c.ask("a", "What is the pressure of P01?", lines)
    r2 = c.ask("b", "What is the pressure of P01?", lines)
    want = fingerprint("What is the pressure of P01?", *lines)
    assert r1.context_sha256 == want and r2.context_sha256 == want and r2.status == "CACHED"
    assert c.ask("c", "What is the pressure of P01?", ["P01 pressure 40 "]).context_sha256 != want


def test_tier1_parse_supported_and_fail_closed():
    from companion.tier1 import parse_tier1_output, evidence_in_context
    good = parse_tier1_output('{"answer": "40", "status": "SUPPORTED", "evidence": ["P01 pressure 40"], "reason": "ok", "should_escalate": false}')
    assert good.is_valid() and good.status == "SUPPORTED" and good.answer == "40"
    assert evidence_in_context(good.evidence, ["P01 pressure 40", "noise"])
    assert not evidence_in_context(good.evidence, ["P01 pressure 41"])
    for bad in (
        "",
        "not json",
        '{"status": "SUPPORTED", "answer": "40", "evidence": [], "should_escalate": false}',
        '{"status": "SUPPORTED", "answer": "40", "evidence": ["x"], "should_escalate": true}',
        '{"status": "MAYBE", "answer": "40", "evidence": ["x"], "should_escalate": false}',
        '{"status": "UNCERTAIN", "should_escalate": false}',
    ):
        r = parse_tier1_output(bad)
        assert r.status == "ESCALATE" or not r.is_valid() or r.should_escalate


def test_tier1_never_overrides_tier0_conflict():
    from companion import Companion, AlwaysEscalateTier1
    from companion.llm import OracleModel
    class AcceptAll:
        def model_id(self): return "accept-all"
        def complete(self, p):
            import json
            return json.dumps({"answer": "99", "status": "SUPPORTED",
                               "evidence": ["fake"], "reason": "x", "should_escalate": False}), 1, 1
    lines = ["P01 pressure 40", "P01 pressure 41"]
    c = Companion(OracleModel(), tier1=AcceptAll())
    r = c.ask("c", "What is the pressure of P01?", lines)
    assert r.status == "UNCERTAIN" or r.delegated_to == "large_model"
    assert r.delegated_to != "tier1"


def test_tier1_stub_escalates_open_questions():
    from companion import Companion, AlwaysEscalateTier1
    from companion.llm import OracleModel
    c = Companion(OracleModel(), tier1=AlwaysEscalateTier1())
    r = c.ask("o", "Which RUNNING asset is closest to overheating?", ["P01 temperature 90", "P01 status RUNNING"])
    assert r.delegated_to == "large_model"


def test_tier1_defaults_to_port_8081():
    from companion.tier1 import LlamaServerTier1
    b = LlamaServerTier1()
    assert b.url == "http://127.0.0.1:8081"
    assert b.n_predict == 96


def test_tier1_model_identity_and_mismatch_fail_closed(monkeypatch):
    from companion.tier1 import LlamaServerTier1
    import json

    class FakeResp:
        def __init__(self, data):
            self._data = data
        def read(self):
            return json.dumps(self._data).encode()
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass

    def fake_urlopen(req, timeout=30):
        url = req if isinstance(req, str) else req.full_url
        if url.endswith("/props"):
            return FakeResp({"model_path": "/models/qwen2.5-0.5b-instruct-q4_k_m.gguf"})
        raise AssertionError(f"unexpected url {url}")

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    b = LlamaServerTier1(url="http://127.0.0.1:8081")
    assert "qwen2.5-0.5b" in b.model_id()

    try:
        LlamaServerTier1(url="http://127.0.0.1:8081", expected_model="other-model.gguf")
        assert False, "expected RuntimeError on model mismatch"
    except RuntimeError as e:
        assert "mismatch" in str(e).lower() or "expected" in str(e).lower()


def test_tier1_cache_hit_preserves_evidence():
    from companion import Companion
    from companion.llm import OracleModel
    import json

    class AcceptWithEvidence:
        def model_id(self):
            return "mock-tier1"
        def complete(self, p):
            return json.dumps({
                "answer": "42",
                "status": "SUPPORTED",
                "evidence": ["SENSOR reading 42"],
                "reason": "mock",
                "should_escalate": False,
            }), 10, 5

    lines = ["SENSOR reading 42", "noise"]
    q = "What reading did SENSOR report?"
    c = Companion(OracleModel(), tier1=AcceptWithEvidence())
    r1 = c.ask("a", q, lines)
    assert r1.delegated_to == "tier1"
    assert r1.status == "SUPPORTED"
    assert r1.evidence == ["SENSOR reading 42"]
    r2 = c.ask("b", q, lines)
    assert r2.status == "CACHED"
    assert r2.cached_origin == "tier1"
    assert r2.evidence == ["SENSOR reading 42"]
    assert r2.context_sha256 == r1.context_sha256


def test_tier1_tokens_included_in_total_cost_metrics():
    from companion import Companion
    from companion.llm import OracleModel
    import json

    class AcceptWithEvidence:
        def model_id(self):
            return "mock-tier1"
        def complete(self, p):
            return json.dumps({
                "answer": "7",
                "status": "SUPPORTED",
                "evidence": ["val 7"],
                "reason": "mock",
                "should_escalate": False,
            }), 100, 20

    c = Companion(OracleModel(), tier1=AcceptWithEvidence())
    r = c.ask("t", "What is val?", ["val 7"])
    assert r.delegated_to == "tier1"
    assert r.large_prompt_tokens == 100
    assert r.large_completion_tokens == 20

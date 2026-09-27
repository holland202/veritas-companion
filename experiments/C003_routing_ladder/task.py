"""C003 task: a timestamped plant log (no two lines byte-identical except deliberate copies), a ladder of question
kinds, and planted traps. Every question carries its ground truth and the status a careful tier 0 should return."""
import numpy as np

FIELDS = ("pressure", "temperature", "status")


def make_task(seed, n_assets=10):
    rng = np.random.default_rng(seed)
    t = iter(sorted(rng.choice(np.arange(1, 9999), 400, replace=False).tolist()))
    ts = lambda: f"t={next(t):04d}"  # noqa: E731
    A = [f"P{i:02d}" for i in range(1, n_assets + 1)]
    facts = {(a, "pressure"): str(int(rng.integers(20, 81))) for a in A}
    facts.update({(a, "temperature"): str(int(rng.integers(40, 96))) for a in A})
    facts.update({(a, "status"): ("RUNNING" if rng.random() < 0.6 else "STOPPED") for a in A})
    ev = []  # (line, tags)
    for (a, f), v in facts.items():
        for _ in range(3):
            ev.append((f"{ts()} {a} {f} {v}", {("fact", a, f)}))
    conflicted = list(rng.choice(A, 2, replace=False))
    for a in conflicted:  # a second source that disagrees, with no UPDATE marker: the log cannot say which is right
        ev.append((f"{ts()} {a} pressure {int(facts[(a, 'pressure')]) + int(rng.integers(5, 20))}", {("fact", a, "pressure")}))
    decoyed = [a for a in A if a not in conflicted][:3]
    for a in decoyed:
        ev.append((f"{ts()} {a} pressure_setpoint {int(rng.integers(20, 99))}", set()))
    restarts = {a: int(rng.integers(0, 4)) for a in A}
    for a, k in restarts.items():
        for _ in range(k):
            line = f"{ts()} {a} restart"
            ev += [(line, {("restart", a)})] * int(rng.integers(1, 3))  # a restart may be logged twice, verbatim
    task_asset = {n: str(rng.choice(A)) for n in range(1, 7)}
    bad_task = 6
    for n, a in task_asset.items():
        line = f"{ts()} TASK {n} start {a}"
        ev += [(line, {("task", n)})] * int(rng.integers(1, 3))
    other = [x for x in A if x != task_asset[bad_task]][0]
    ev.append((f"{ts()} TASK {bad_task} start {other}", {("task", bad_task)}))
    stop_t, start_t = {}, {}
    for a in A:
        s1, s2 = next(t), next(t)
        stop_t[a], start_t[a] = s1, s2
        ev.append((f"t={s1:04d} {a} stop", {("stop", a)}))
        ev.append((f"t={s2:04d} {a} start", {("start", a)}))
    ev += [(f"{ts()} heartbeat seq={int(rng.integers(1e5))} ok", set()) for _ in range(20)]
    order = rng.permutation(len(ev))
    lines = [ev[i][0] for i in order]
    tags = [ev[i][1] for i in order]

    qs = []
    plain = [a for a in A if a not in conflicted]
    for a in list(rng.choice(plain, 4, replace=False)):
        f = str(rng.choice(FIELDS)) if a not in decoyed else "pressure"
        qs.append(dict(q=f"What is the {f} of {a}?", truth=facts[(a, f)], expect="SUPPORTED", kind="L0 lookup",
                       need={("fact", a, f)}))
    for a in conflicted:
        qs.append(dict(q=f"What is the pressure of {a}?", truth=None, expect="UNCERTAIN", kind="L0 conflict",
                       need={("fact", a, "pressure")}))
    for a in list(rng.choice(A, 3, replace=False)):
        qs.append(dict(q=f"How many times did {a} restart?", truth=str(restarts[a]), expect="SUPPORTED",
                       kind="L1 count", need={("restart", a)} if restarts[a] else set()))
    for n in (1, 2, bad_task):
        qs.append(dict(q=f"Which asset did TASK {n} act on?", truth=None if n == bad_task else task_asset[n],
                       expect="UNCERTAIN" if n == bad_task else "SUPPORTED",
                       kind="L2 conflict" if n == bad_task else "L2 relation", need={("task", n)}))
    for _ in range(3):
        a, b = rng.choice(A, 2, replace=False)
        qs.append(dict(q=f"Did {a} stop before {b} started?", truth="yes" if stop_t[a] < start_t[b] else "no",
                       expect="SUPPORTED", kind="L3 order", need={("stop", a), ("start", b)}))
    running = [a for a in A if facts[(a, "status")] == "RUNNING"] or A
    hot = max(running, key=lambda a: int(facts[(a, "temperature")]))
    qs.append(dict(q="Which RUNNING asset is closest to overheating, judging by temperature?", truth=hot,
                   expect="ESCALATE", kind="L4 judgement", need={("fact", a, "temperature") for a in A}))
    return lines, tags, qs

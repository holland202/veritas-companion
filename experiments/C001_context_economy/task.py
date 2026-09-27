"""A redundant plant log and questions about it, with ground truth. Seeded and deterministic."""
import numpy as np

FIELDS = ("pressure", "temperature", "status")


def make_task(seed, n_assets=12, repeats=4, n_noise=30, n_conflicts=4, asks_each=3):
    rng = np.random.default_rng(seed)
    assets = [f"P{i:02d}" for i in range(1, n_assets + 1)]
    facts = {}
    for a in assets:
        facts[(a, "pressure")] = str(int(rng.integers(20, 81)))
        facts[(a, "temperature")] = str(int(rng.integers(40, 96)))
        facts[(a, "status")] = "RUNNING" if rng.random() < 0.6 else "STOPPED"
    base = [f"{a} {f} {facts[(a, f)]}" for a in assets for f in FIELDS]
    early = base * repeats + [f"heartbeat seq={int(s)} ok" for s in rng.choice(100000, n_noise, replace=False)]
    early = [early[i] for i in rng.permutation(len(early))]
    conflicted = [assets[i] for i in rng.choice(n_assets, n_conflicts, replace=False)]
    late = []
    for a in conflicted:
        old = int(facts[(a, "pressure")])
        new = old + int(rng.integers(3, 15))
        facts[(a, "pressure")] = str(new)
        late += [f"UPDATE {a} pressure {new}"] * 2
    late = [late[i] for i in rng.permutation(len(late))]
    lines = early + late
    plain = [a for a in assets if a not in conflicted]
    qs = []
    for a in rng.choice(plain, 5, replace=False):
        f = FIELDS[int(rng.integers(3))]
        qs.append((f"What is the {f} of {a}?", facts[(a, f)], "lookup"))
    for a in conflicted[:3]:
        qs.append((f"What is the pressure of {a}?", facts[(a, "pressure")], "conflict"))
    running = [a for a in assets if facts[(a, "status")] == "RUNNING"]
    hot = max(running, key=lambda a: int(facts[(a, "temperature")]))
    low = min(running, key=lambda a: int(facts[(a, "pressure")]))
    qs.append(("Which RUNNING asset has the highest temperature?", hot, "aggregate"))
    qs.append(("Which RUNNING asset has the lowest pressure?", low, "aggregate"))
    asks = [q for q in qs for _ in range(asks_each)]
    asks = [asks[i] for i in rng.permutation(len(asks))]
    return lines, asks

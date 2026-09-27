"""More tier-0 tools (C003): counting, relations, ordering in time. Each returns a Result, or None when the
question is not its kind. They answer only from lines they can point to, and say UNCERTAIN or ESCALATE rather
than guess."""
import re

from .runtime_types import Result

TS = r"t=(\d+) "
COUNT = re.compile(r"^How many times did (P\d+) restart\?$")
RELATION = re.compile(r"^Which asset did TASK (\d+) act on\?$")
BEFORE = re.compile(r"^Did (P\d+) stop before (P\d+) started\?$")


def _events(lines, pattern):
    pat = re.compile(pattern)
    return [(m, ln) for ln in lines if (m := pat.search(ln.strip()))]


def count_tool(lines, q):
    m = COUNT.match(q)
    if not m:
        return None
    hits = _events(lines, rf"^{TS}{re.escape(m.group(1))} restart$")
    stamps = sorted({h[0].group(1) for h in hits})  # one restart per timestamp: copies of a line are one event
    return Result("SUPPORTED", str(len(stamps)), [ln for _, ln in hits][:3])


def relation_tool(lines, q):
    m = RELATION.match(q)
    if not m:
        return None
    hits = _events(lines, rf"^{TS}TASK {m.group(1)} start (P\d+)$")
    assets = list(dict.fromkeys(h[0].group(2) for h in hits))
    if len(assets) == 1:
        return Result("SUPPORTED", assets[0], [ln for _, ln in hits][:3])
    return Result("UNCERTAIN" if assets else "ESCALATE", None, [ln for _, ln in hits][:3])


def before_tool(lines, q):
    m = BEFORE.match(q)
    if not m:
        return None
    a, b = m.groups()
    stops = _events(lines, rf"^{TS}{re.escape(a)} stop$")
    starts = _events(lines, rf"^{TS}{re.escape(b)} start$")
    if not stops or not starts:
        return Result("ESCALATE")
    ta = min(int(h[0].group(1)) for h in stops)
    tb = min(int(h[0].group(1)) for h in starts)
    ev = [stops[0][1], starts[0][1]]
    if ta == tb:
        return Result("UNCERTAIN", None, ev)
    return Result("SUPPORTED", "yes" if ta < tb else "no", ev)


TOOLS = (count_tool, relation_tool, before_tool)

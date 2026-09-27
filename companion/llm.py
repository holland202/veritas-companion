"""Model backends. LlamaServer talks to a llama.cpp server (stdlib only). OracleModel exists for code tests:
it reads the answer out of the context by rule, so any number produced with it is NOT A RESULT."""
import json
import re
import urllib.request


class LlamaServer:
    is_real = True

    def __init__(self, url="http://127.0.0.1:8080", n_predict=16, seed=0):
        self.url, self.n_predict, self.seed = url.rstrip("/"), n_predict, seed

    def _post(self, path, body):
        req = urllib.request.Request(self.url + path, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read())

    def model_id(self):
        with urllib.request.urlopen(self.url + "/props", timeout=30) as r:
            p = json.loads(r.read())
        return str(p.get("model_path") or p.get("default_generation_settings", {}).get("model", "unknown"))

    def count_tokens(self, text):
        return len(self._post("/tokenize", {"content": text})["tokens"])

    def complete(self, prompt):
        """Returns (text, prompt_tokens, completion_tokens)."""
        r = self._post("/completion", {"prompt": prompt, "n_predict": self.n_predict, "temperature": 0,
                                       "seed": self.seed, "cache_prompt": True, "stop": ["\n"]})
        t = r.get("timings", {})
        prompt_tokens = self.count_tokens(prompt)  # the whole prompt, cached or not: the cost being compared
        completion_tokens = int(r.get("tokens_predicted", t.get("predicted_n", 0)))
        return r.get("content", "").strip(), prompt_tokens, completion_tokens


class OracleModel:
    """Test double. Answers lookups and the 'highest' question by rule from the context it is given, so it
    loses information exactly when the context does. Token cost = whitespace-separated words."""
    is_real = False

    def model_id(self):
        return "oracle-test-double"

    def count_tokens(self, text):
        return len(text.split())

    def complete(self, prompt):
        ctx, q = prompt.split("Question:", 1)
        q = q.split("\n")[0].strip()
        latest = {}
        for line in ctx.splitlines():
            m = re.match(r"^(?:UPDATE )?(P\d+) (pressure|temperature|status) (\S+)", line.strip())
            if m:
                latest[(m.group(1), m.group(2))] = m.group(3)
        kvq = re.match(r"What is the value of (.+)\?$", q)
        if kvq:
            from .kv import norm_key, parse_kv
            last = None
            for line in ctx.splitlines():
                kv = parse_kv(line)
                if kv and kv[0] == norm_key(kvq.group(1)):
                    last = kv[1]
            return (last or "unknown"), self.count_tokens(prompt), 1
        m = re.match(r"What is the (\w+) of (P\d+)\?", q)
        if m:
            ans = latest.get((m.group(2), m.group(1)), "unknown")
        else:
            fld = "temperature" if "temperature" in q else "pressure"
            vals = {a: float(v) for (a, f), v in latest.items() if f == fld and latest.get((a, "status")) == "RUNNING"}
            pick = max if "highest" in q else min
            ans = pick(vals, key=vals.get) if vals else "unknown"
        return ans, self.count_tokens(prompt), 1

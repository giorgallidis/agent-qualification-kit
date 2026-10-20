"""Pluggable model adapters. Every adapter turns (system, prompt) into a
response — that's the entire extension point. Add your own by subclassing
Adapter and registering it in get_adapter() below.

Credentials are read from environment variables ONLY. Never pass a key as a
CLI argument or hard-code one — pass the NAME of the env var instead.
"""
import json
import os
import re
import urllib.error
import urllib.request

from common import seeded_random


class Adapter:
    def generate(self, *, system, prompt, temperature=0.3):
        """Returns {"text": str, "cost_usd": float, "model": str}."""
        raise NotImplementedError


class StubAdapter(Adapter):
    """Offline, deterministic. No network, no keys. This is what --dry-run
    uses, so anyone can run the whole pipeline in under a minute and see the
    shape of every file it produces before spending a cent."""

    name = "stub"

    def generate(self, *, system, prompt, temperature=0.3):
        rnd = seeded_random(prompt[:4000] + (system or ""))
        mode = _mode(prompt)
        if mode == "RUBRIC_JUDGE":
            text = _rubric_json(rnd)
        elif mode == "PAIRWISE_JUDGE":
            text = _pairwise_json(rnd)
        else:
            text = _draft(prompt, system)
        return {"text": text, "cost_usd": round(rnd.uniform(0.002, 0.01), 4), "model": "stub-v1"}


class OpenAICompatibleAdapter(Adapter):
    """Works with OpenAI itself and any OpenAI-compatible chat/completions
    endpoint (self-hosted, or another vendor's compatible API)."""

    name = "openai_compatible"

    def __init__(self, model, base_url=None, api_key_env="OPENAI_API_KEY",
                 price_per_1k_input=0.0, price_per_1k_output=0.0):
        self.model = model
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.api_key = os.environ.get(api_key_env)
        if not self.api_key:
            raise RuntimeError(f"Set {api_key_env} in your environment first (never pass keys as CLI flags).")
        # Pricing is never guessed here: pass your provider's own published
        # $/1K-token rates, or leave both at 0 and cost-per-accepted-output
        # will simply read as $0.00 for this adapter.
        self.price_in = price_per_1k_input
        self.price_out = price_per_1k_output

    def generate(self, *, system, prompt, temperature=0.3):
        messages = ([{"role": "system", "content": system}] if system else []) + [
            {"role": "user", "content": prompt}
        ]
        body = json.dumps({"model": self.model, "messages": messages, "temperature": temperature}).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"{self.base_url}: {e.code} {e.read().decode()[:300]}")
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        cost = (
            usage.get("prompt_tokens", 0) / 1000 * self.price_in
            + usage.get("completion_tokens", 0) / 1000 * self.price_out
        )
        return {"text": text, "cost_usd": round(cost, 6), "model": data.get("model", self.model)}


def get_adapter(name, **kwargs):
    if name in ("stub", "dry-run", "dry_run"):
        return StubAdapter()
    if name in ("openai", "openai_compatible"):
        return OpenAICompatibleAdapter(**kwargs)
    raise ValueError(f"Unknown adapter '{name}'. Add your own in harness/adapters.py and register it here.")


# --- stub helpers -----------------------------------------------------------
def _mode(prompt):
    m = re.search(r"MODE:\s*(\w+)", prompt)
    return m.group(1) if m else "GENERATION"


def _draft(prompt, system):
    tid = re.search(r"TASK_ID:\s*(\S+)", prompt)
    tid = tid.group(1) if tid else "T?"
    ask = "\n".join(l for l in prompt.splitlines() if l.strip())[:600]
    body = (
        f"# Draft for {tid}\n\n"
        "status: DRAFT - needs human approval\n\n"
        "This is a stub response for --dry-run testing. Swap in a real adapter to see what "
        "an actual model produces for this task.\n\n"
        "## Task (as given to this run)\n"
        f"{ask}\n\n"
        "## Draft\n"
        "[stub placeholder body — a real model fills this in from the task card and sources above]\n"
    )
    if system:
        # Simulates a real difference between the agent arm (has a persona/instructions)
        # and the baseline arm (task card + sources only) without naming either arm in
        # the text itself — the blinding step should not have anything to strip here.
        body += (
            "\n## Self-check\n"
            "- Stays within the facts sheet; nothing stated as true beyond it or the named sources.\n"
            "- No banned claim used.\n"
        )
    return body


def _rubric_json(rnd):
    scores = {c: rnd.choice([3, 4, 4, 5]) for c in ("accuracy", "voice", "specificity", "actionability", "policy")}
    hard_fail = scores["accuracy"] == 1 or scores["policy"] == 1
    return json.dumps(
        {
            **scores,
            "hard_fail": hard_fail,
            "hard_fail_reason": "" if not hard_fail else "stub hard fail",
            "task_coverage": rnd.choice([80, 90, 100]),
            "rationale": "Stub judge: placeholder scoring for dry-run testing only, not a real evaluation.",
            "violations": [] if rnd.random() > 0.3 else ["stub: minor word-limit overrun"],
        }
    )


def _pairwise_json(rnd):
    winner = rnd.choice(["1", "2"])
    return json.dumps(
        {
            "winner": winner,
            "reason": f"Stub judge: Response {winner} looks more complete and closer to the sources (placeholder reasoning).",
        }
    )

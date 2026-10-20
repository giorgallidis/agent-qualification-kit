"""Shared helpers for the Agent Qualification Kit harness scripts."""
import hashlib
import json
import os
import random
import re

CRITERIA = ["accuracy", "voice", "specificity", "actionability", "policy"]


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path, text):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def write_json(path, obj):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1)


TASK_RE = re.compile(r"^##\s+(?P<id>T\d+)\s*\(agent:\s*(?P<agent>[^)]+)\)\s*$", re.M)


def parse_tasks(process_dir):
    """Parse <process_dir>/tasks.md into a list of
    {"id": "T1", "agent": "...", "text": "...", "sources": [...]}.

    Format (see templates/task-card-template.md):
        ## T1 (agent: <name>)
        <task text>

        Sources:
        - path/one
        - path/two
    """
    path = os.path.join(process_dir, "tasks.md")
    content = read(path)
    matches = list(TASK_RE.finditer(content))
    tasks = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end].strip()
        sources = []
        src_match = re.search(r"Sources:\s*\n((?:\s*-\s*.+\n?)+)", body)
        if src_match:
            sources = [s.strip("- ").strip() for s in src_match.group(1).splitlines() if s.strip()]
            body = body[: src_match.start()].strip()
        tasks.append({"id": m.group("id"), "agent": m.group("agent").strip(), "text": body, "sources": sources})
    return tasks


def seeded_random(key):
    return random.Random(hashlib.sha256(key.encode("utf-8")).hexdigest())


def redact(text, terms):
    out = text
    for t in terms:
        t = t.strip()
        if not t:
            continue
        out = re.sub(re.escape(t), "[redacted]", out, flags=re.I)
    return out

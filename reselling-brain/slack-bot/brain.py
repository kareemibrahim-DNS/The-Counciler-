"""Reselling Brain core: loads the shared knowledge files and asks Claude.

The same knowledge folder feeds the Claude Skill and Orbit, so an update in
../knowledge reaches every surface.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import anthropic
import yaml

KNOWLEDGE_DIR = Path(os.environ.get("BRAIN_KNOWLEDGE_DIR", Path(__file__).resolve().parent.parent / "knowledge"))
LAYERS_FILE = Path(os.environ.get("BRAIN_LAYERS_FILE", Path(__file__).resolve().parent / "layers.yaml"))
MODEL = os.environ.get("BRAIN_MODEL", "claude-sonnet-5-5")
MAX_TOKENS = int(os.environ.get("BRAIN_MAX_TOKENS", "1500"))

_FRONT = re.compile(r"^---\n(.*?)\n---\n", re.S)


@dataclass(frozen=True)
class Doc:
    id: str
    audience: str
    body: str


def owner_docs_from_env(value: str | None = None) -> list[Doc]:
    """Owner-only knowledge (pricing/markups, targets, contacts, gaps) never lives in this shared repo.

    It comes from the BRAIN_OWNER_KNOWLEDGE_B64 secret: base64 of a JSON list of {id, body}.
    Every doc loaded this way is forced to audience "owner", whatever the payload says.
    """
    import base64
    import json
    raw = os.environ.get("BRAIN_OWNER_KNOWLEDGE_B64", "") if value is None else value
    if not raw.strip():
        return []
    items = json.loads(base64.b64decode(raw).decode("utf-8"))
    return [Doc(id=str(i["id"]), audience="owner", body=str(i["body"]).strip()) for i in items if i.get("id") and i.get("body")]


def load_docs(folder: Path = KNOWLEDGE_DIR) -> list[Doc]:
    docs = []
    for path in sorted(folder.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta, body = {}, text
        m = _FRONT.match(text)
        if m:
            meta = yaml.safe_load(m.group(1)) or {}
            body = text[m.end():]
        # Fail closed: a file with no audience tag is treated as owner-only.
        docs.append(Doc(id=str(meta.get("id", path.stem)), audience=str(meta.get("audience", "owner")), body=body.strip()))
    return docs + owner_docs_from_env()


def load_layers(path: Path = LAYERS_FILE) -> dict:
    if not path.exists():
        return {"levels": {"owner": {"sees": ["owner", "team"]}, "team": {"sees": ["team"]},
                           "sales": {"sees": ["sales"], "tools": ["brain_catalog"]}},
                "people": {}, "default_level": "sales"}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


DEFAULT_BLOCKED_CHANNELS = [r"^(ksa|uae|egypt|kw-jo|kw|jo|eg)-", r"^foodics-"]
PARTNER_SPACE_REPLY = ("I don't answer in channels that partners can read. "
                       "Please DM me, or ask in an internal Foodics channel.")


def partner_space(*, channel_name: str | None, is_shared: bool, is_im: bool, user_team: str | None,
                  workspace_team: str | None, layers: dict) -> bool:
    """True when a partner could read the reply or is the one asking: never answer there.

    Partner members sit in per-partner channels (#ksa-grubtech, #foodics-urbanpiper) and in
    Slack Connect channels; Slack Connect users come from another workspace (user_team differs).
    """
    if user_team and workspace_team and user_team != workspace_team:
        return True
    if is_im:
        return False
    if is_shared:
        return True
    patterns = layers.get("blocked_channels") or DEFAULT_BLOCKED_CHANNELS
    allowed = set(layers.get("allowed_channels") or [])
    name = (channel_name or "").lstrip("#").lower()
    if name in allowed:
        return False
    return any(re.search(p, name) for p in patterns)


def level_for(slack_user_id: str, layers: dict) -> str:
    people = layers.get("people") or {}
    # Deny by default: anyone not listed gets the most limited layer.
    return str((people.get(slack_user_id) or {}).get("level", layers.get("default_level", "sales")))


def visible_docs(level: str, layers: dict, docs: list[Doc]) -> list[Doc]:
    sees = set((layers.get("levels") or {}).get(level, {}).get("sees", ["sales"]))
    return [d for d in docs if d.audience in sees]


def system_prompt(level: str, layers: dict, docs: list[Doc]) -> str:
    parts = [f"<knowledge id=\"{d.id}\">\n{d.body}\n</knowledge>" for d in visible_docs(level, layers, docs)]
    level_note = (layers.get("levels") or {}).get(level, {}).get("instructions", "")
    footer = f"\n\nThe person asking is at level: {level}.\n{level_note}".rstrip()
    if level != "owner":
        footer += ("\nThis person cannot see owner-only material (cost prices, markups, targets, strategy, "
                   "negotiations). If asked for it, say it is restricted and to ask Kareem.")
    return "\n\n".join(parts) + footer


TOOL_GUIDE = """
## Tools
You have read-only tools. Use them whenever the answer depends on current facts (a merchant's ARR or churn,
a partner's latest Slack thread, a ticket's status, a contract clause, an attached file) instead of guessing.
- Say which tool and source each live fact came from.
- If a tool fails or returns nothing, say so plainly; do not invent the result.
- Tools never send or change anything. To "send" something, write a draft for the person to send.
- When drafting a deal or discount email reply, add the Standard T&C block from the policy.
- Use `learn` only when Kareem states a new or corrected rule; tell him it waits for his approval.
"""
MAX_TOOL_TURNS = 8


def tools_for(level: str, layers: dict, tools: dict) -> dict:
    allowed = (layers.get("levels") or {}).get(level, {}).get("tools", [])
    return {k: v for k, v in tools.items() if k in allowed}


class Brain:
    def __init__(self, client: anthropic.Anthropic | None = None, tools: dict | None = None):
        self.client = client or anthropic.Anthropic()
        self.all_tools = tools or {}
        self.reload()

    def reload(self) -> None:
        self.docs = load_docs()
        self.layers = load_layers()

    def ask(self, question: str, slack_user_id: str, history: list[dict] | None = None) -> str:
        level = level_for(slack_user_id, self.layers)
        tools = tools_for(level, self.layers, self.all_tools)
        system = system_prompt(level, self.layers, self.docs) + (TOOL_GUIDE if tools else "")
        messages = list(history or []) + [{"role": "user", "content": question}]
        kwargs = dict(model=MODEL, max_tokens=MAX_TOKENS,
                      # The knowledge block is cached so repeat questions are cheap and fast.
                      system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}])
        if tools:
            kwargs["tools"] = [t["schema"] for t in tools.values()]
        for _ in range(MAX_TOOL_TURNS + 1):
            resp = self.client.messages.create(messages=messages, **kwargs)
            uses = [b for b in resp.content if getattr(b, "type", "") == "tool_use"]
            if not uses or resp.stop_reason != "tool_use":
                return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
            messages.append({"role": "assistant", "content": [b.model_dump() if hasattr(b, "model_dump") else b for b in resp.content]})
            results = []
            for u in uses:
                tool = tools.get(u.name)  # a tool outside this level's list is refused, even if the model asks for it
                try:
                    args = {k: v for k, v in (u.input or {}).items() if not k.startswith("_")}
                    if tool and tool.get("level_aware"):
                        args["_level"] = level
                    out = tool["fn"](**args) if tool else f"Tool '{u.name}' is not available at level {level}."
                    err = tool is None
                except Exception as exc:  # report the failure to the model instead of crashing
                    out, err = f"Tool error: {exc}", True
                results.append({"type": "tool_result", "tool_use_id": u.id, "content": out, "is_error": err})
            messages.append({"role": "user", "content": results})
        return "I needed too many lookups for this one. Please narrow the question."

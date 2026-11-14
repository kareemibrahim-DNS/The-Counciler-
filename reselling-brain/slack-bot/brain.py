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
CATALOG_DIR = Path(os.environ.get("BRAIN_CATALOG_DIR", Path(__file__).resolve().parent.parent / "catalog"))
# Facts Kareem approves as owner-only are kept OUT of knowledge/ (and out of git and the image).
OWNER_LEARNED_FILE = Path(os.environ.get("BRAIN_OWNER_LEARNED_FILE", Path(__file__).resolve().parent / "learned_owner.md"))
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


def owner_docs_from_file(path: Path = OWNER_LEARNED_FILE) -> list[Doc]:
    """Facts Kareem approved as owner-only with `approve <id>`. Always audience owner."""
    if not path.exists():
        return []
    body = _FRONT.sub("", path.read_text(encoding="utf-8")).strip()
    return [Doc(id="learned-owner", audience="owner", body=body)] if body else []


def load_docs(folder: Path = KNOWLEDGE_DIR, private: bool = True) -> list[Doc]:
    """The shared knowledge files, plus (private=True) the owner secret and owner-learned facts."""
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
    return docs + (owner_docs_from_env() + owner_docs_from_file() if private else [])


def load_layers(path: Path = LAYERS_FILE) -> dict:
    if not path.exists():
        return {"levels": {"owner": {"sees": ["owner", "team"]}, "team": {"sees": ["team"]},
                           "sales": {"sees": ["sales"], "tools": ["brain_catalog"]}},
                "people": {}, "default_level": "sales"}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


DEFAULT_BLOCKED_CHANNELS = [r"^(ksa|uae|egypt|kw-jo|kw|jo|eg)-", r"^foodics-"]


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


def level_for(slack_user_id: str, layers: dict, owner_id: str | None = None) -> str:
    """The asker's own level. Deny by default: anyone not listed gets the most limited layer.

    The owner is whoever BRAIN_OWNER_SLACK_ID (a Railway secret) names. An `owner` entry in
    layers.yaml, which lives in the shared repo, is not enough on its own: it becomes sales.
    """
    owner_id = os.environ.get("BRAIN_OWNER_SLACK_ID", "") if owner_id is None else owner_id
    if slack_user_id and owner_id and slack_user_id == owner_id:
        return "owner"
    people = layers.get("people") or {}
    level = str((people.get(slack_user_id) or {}).get("level", layers.get("default_level", "sales")))
    return "sales" if level == "owner" else level


def visible_docs(level: str, layers: dict, docs: list[Doc]) -> list[Doc]:
    sees = set((layers.get("levels") or {}).get(level, {}).get("sees", ["sales"]))
    # Owner material is owner-only whatever layers.yaml says.
    return [d for d in docs if d.audience in sees and (d.audience != "owner" or level == "owner")]


WHERE_NOTES = {
    "dm": "You are answering in a private DM with this person.",
    "channel": ("Your reply will be posted in a Slack channel thread that other people can read. "
                "Answer only at this level, whatever the asker's own access is."),
}


def system_prompt(level: str, layers: dict, docs: list[Doc], where: str = "dm", capped: bool = False) -> str:
    parts = [f"<knowledge id=\"{d.id}\">\n{d.body}\n</knowledge>" for d in visible_docs(level, layers, docs)]
    level_note = (layers.get("levels") or {}).get(level, {}).get("instructions", "")
    footer = f"\n\nThe answer is at level: {level}.\n{level_note}".rstrip()
    footer += "\n" + WHERE_NOTES.get(where, WHERE_NOTES["channel"])
    if capped:
        footer += ("\nThe asker has more access in a private DM. If the question needs more than this level allows, "
                   "say you can only share that in a DM, without hinting at the content.")
    if level != "owner":
        footer += ("\nThis person cannot see owner-only material (cost prices, markups, targets, strategy, "
                   "negotiations). If asked for it, say it is restricted and to ask Kareem.")
    return "\n\n".join(parts) + footer


# ---------- reply safety ----------
DEFAULT_LINK_HOSTS = ("foodics.com", "slack.com", "salesforce.com", "force.com", "google.com", "forms.gle")
_URL = re.compile(r"https?://[^\s<>|()\[\]\"'`]+", re.I)
_HOST = re.compile(r"^https?://([^/:?#]+)", re.I)


def link_hosts(texts: list[str]) -> set[str]:
    """Hosts of the links in our own knowledge and catalogue: the only links a reply may carry."""
    hosts = set(DEFAULT_LINK_HOSTS)
    for t in texts:
        for url in _URL.findall(t or ""):
            m = _HOST.match(url)
            if m:
                hosts.add(m.group(1).lower())
    return hosts


def _host_ok(url: str, hosts: set[str]) -> bool:
    m = _HOST.match(url)
    host = m.group(1).lower() if m else ""
    return bool(host) and any(host == h or host.endswith("." + h) for h in hosts)


def safe_reply(text: str, hosts: set[str]) -> str:
    """Remove links to unknown hosts (a prompt-injection exfiltration path) and @channel-style pings."""
    text = _URL.sub(lambda m: m.group(0) if _host_ok(m.group(0), hosts) else "[link removed]", text or "")
    return re.sub(r"<!(channel|here|everyone|subteam\^[A-Z0-9]+)[^>]*>", r"@\1", text)


SALES_TOOL_GUIDE = """
## Tools
- Call `brain_catalog` for every partner, line item and price. Never quote a price from memory.
- If the tool fails or returns nothing, say so plainly; do not invent the result.
"""
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
LEVEL_RANK = {"sales": 0, "team": 1, "owner": 2}


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
        catalog = [p.read_text(encoding="utf-8") for p in sorted(CATALOG_DIR.glob("*.json"))] if CATALOG_DIR.exists() else []
        self.link_hosts = link_hosts([d.body for d in self.docs] + catalog)

    def level_of(self, slack_user_id: str) -> str:
        return level_for(slack_user_id, self.layers)

    def ask(self, question: str, slack_user_id: str, history: list[dict] | None = None, *,
            level: str | None = None, where: str = "dm", ctx: dict | None = None) -> str:
        """`level` caps the answer (it can only lower the asker's own level); `where` says who reads it."""
        own = level_for(slack_user_id, self.layers)
        level = own if level is None else (level if LEVEL_RANK.get(level, -1) <= LEVEL_RANK.get(own, -1) else own)
        if LEVEL_RANK.get(level, -1) < 0:
            level = "sales"
        capped = LEVEL_RANK.get(level, -1) < LEVEL_RANK.get(own, -1)
        tools = tools_for(level, self.layers, self.all_tools)
        guide = (SALES_TOOL_GUIDE if level == "sales" else TOOL_GUIDE) if tools else ""
        system = system_prompt(level, self.layers, self.docs, where=where, capped=capped) + guide
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
                    if tool and tool.get("ctx_aware"):
                        args["_ctx"] = dict(ctx or {})
                    out = tool["fn"](**args) if tool else f"Tool '{u.name}' is not available at level {level}."
                    err = tool is None
                except Exception as exc:  # report the failure to the model instead of crashing
                    out, err = f"Tool error: {exc}", True
                results.append({"type": "tool_result", "tool_use_id": u.id, "content": out, "is_error": err})
            messages.append({"role": "user", "content": results})
        return "I needed too many lookups for this one. Please narrow the question."

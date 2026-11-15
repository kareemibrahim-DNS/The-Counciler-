"""Reselling Brain core: loads the shared knowledge files and asks Claude.

The same knowledge folder feeds the Slack bot and the common-layer Claude skill,
so an update in ../knowledge reaches every surface. This repo is the only home.
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
# Facts Kareem shares with the team (`approve <id> team`) are team-only, so they stay out of the repo too.
TEAM_LEARNED_FILE = Path(os.environ.get("BRAIN_TEAM_LEARNED_FILE", Path(__file__).resolve().parent / "learned_team.md"))
LAYERS_FILE = Path(os.environ.get("BRAIN_LAYERS_FILE", Path(__file__).resolve().parent / "layers.yaml"))
MODEL = os.environ.get("BRAIN_MODEL", "claude-sonnet-5-5")
MAX_TOKENS = int(os.environ.get("BRAIN_MAX_TOKENS", "1500"))

_FRONT = re.compile(r"^---\n(.*?)\n---\n", re.S)


@dataclass(frozen=True)
class Doc:
    id: str
    audience: str
    body: str


# Audiences (Kareem, 14 Nov 2026):
#   base    everyone at Foodics: resellers, list prices, quotes, comparisons, merchant fit, flows, unified billing
#   sales   instructions for the base level only (what is locked and how to point to the flow)
#   team    Partnerships team: policy, discount eligibility, SLAs, processes, partner operations
#   manager managers: program cycles, targets, strategy, internal trackers, partner contacts
#   cost    cost prices and contracts: only the people in BRAIN_COST_SLACK_IDS (Hatem) and Kareem
#   owner   Kareem only
PRIVATE_AUDIENCES = ("team", "manager", "cost", "owner")  # only ever loaded from the secret, never from this repo
REPO_AUDIENCES = ("base", "sales")  # the shared repo holds the common layer only


def owner_docs_from_env(value: str | None = None) -> list[Doc]:
    """Everything above the common layer (team policy and processes, contacts, cycles and strategy, cost and
    contracts, gaps) lives only in the BRAIN_OWNER_KNOWLEDGE_B64 secret, never in this shared repo.

    The secret is base64 of a JSON list of {id, body, audience?}. audience may be team, manager, cost or owner;
    anything else (or nothing) is forced to owner. Items without a body (team catalogue notes) are not docs.
    """
    import base64
    import json
    raw = os.environ.get("BRAIN_OWNER_KNOWLEDGE_B64", "") if value is None else value
    if not raw.strip():
        return []
    items = json.loads(base64.b64decode(raw).decode("utf-8"))
    return [Doc(id=str(i["id"]), audience=i.get("audience") if i.get("audience") in PRIVATE_AUDIENCES else "owner",
                body=str(i["body"]).strip()) for i in items if i.get("id") and i.get("body")]


def owner_docs_from_file(path: Path = OWNER_LEARNED_FILE) -> list[Doc]:
    """Facts Kareem approved as owner-only with `approve <id>`. Always audience owner."""
    if not path.exists():
        return []
    body = _FRONT.sub("", path.read_text(encoding="utf-8")).strip()
    return [Doc(id="learned-owner", audience="owner", body=body)] if body else []


def team_docs_from_file(path: Path = TEAM_LEARNED_FILE) -> list[Doc]:
    """Facts Kareem shared with `approve <id> team`. Always audience team, never in the repo."""
    if not path.exists():
        return []
    body = _FRONT.sub("", path.read_text(encoding="utf-8")).strip()
    return [Doc(id="learned-team", audience="team", body=body)] if body else []


def load_docs(folder: Path = KNOWLEDGE_DIR, private: bool = True) -> list[Doc]:
    """The shared knowledge files (common layer), plus (private=True) the secret and the learned facts."""
    docs = []
    for path in sorted(folder.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta, body = {}, text
        m = _FRONT.match(text)
        if m:
            meta = yaml.safe_load(m.group(1)) or {}
            body = text[m.end():]
        # Fail closed: a repo file may only be common layer; anything else (or no tag) is treated as owner-only.
        audience = str(meta.get("audience", "owner"))
        docs.append(Doc(id=str(meta.get("id", path.stem)), audience=audience if audience in REPO_AUDIENCES else "owner",
                        body=body.strip()))
    return docs + (owner_docs_from_env() + team_docs_from_file() + owner_docs_from_file() if private else [])


def load_layers(path: Path = LAYERS_FILE) -> dict:
    if not path.exists():
        return {"levels": {"owner": {"sees": ["owner", "cost", "manager", "team", "base"]},
                           "manager": {"sees": ["manager", "team", "base"]}, "team": {"sees": ["team", "base"]},
                           "sales": {"sees": ["sales", "base"], "tools": ["brain_catalog", "escalate"]}},
                "people": {}, "default_level": "sales"}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


DEFAULT_BLOCKED_CHANNELS = [r"^(ksa|uae|egypt|kw-jo|kw|jo|eg)-", r"^foodics-"]


def partner_space(*, channel_name: str | None, is_shared: bool, is_im: bool, user_team: str | None,
                  workspace_team: str | None, layers: dict) -> bool:
    """True when a partner could read the reply or is the one asking: never answer there.

    Partner members sit in per-partner channels (named ksa-…, uae-…, egypt-…, kw-jo-…, foodics-…) and in
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


def cost_access(slack_user_id: str, value: str | None = None) -> bool:
    """Cost prices and contracts: only the Slack IDs in the BRAIN_COST_SLACK_IDS secret (Hatem). Kareem has owner."""
    raw = os.environ.get("BRAIN_COST_SLACK_IDS", "") if value is None else value
    return bool(slack_user_id) and slack_user_id in {x.strip() for x in raw.split(",") if x.strip()}


def visible_docs(level: str, layers: dict, docs: list[Doc], cost: bool = False) -> list[Doc]:
    """Docs this level may see. Hard limits apply whatever layers.yaml (a shared file) says:
    owner docs only at owner level; cost docs only for the owner or a cost grant; manager docs only from manager up."""
    sees = set((layers.get("levels") or {}).get(level, {}).get("sees", ["sales", "base"]))

    def allowed(d: Doc) -> bool:
        if d.audience == "base":
            return True  # the common layer everyone at Foodics sees
        if d.audience == "owner":
            return level == "owner"
        if d.audience == "cost":
            return level == "owner" or (cost and LEVEL_RANK.get(level, -1) >= LEVEL_RANK["manager"])
        if d.audience == "manager":
            return LEVEL_RANK.get(level, -1) >= LEVEL_RANK["manager"] and d.audience in sees
        return d.audience in sees
    return [d for d in docs if allowed(d)]


WHERE_NOTES = {
    "dm": "You are answering in a private DM with this person.",
    "channel": ("Your reply will be posted in a Slack channel thread that other people can read. "
                "Answer only at this level, whatever the asker's own access is."),
}


COUNTRY_NAMES = {"SA": "KSA (SAR)", "AE": "UAE (AED)", "KW": "Kuwait (KWD)", "JO": "Jordan (JOD)", "EG": "Egypt (EGP)",
                 "INT": "International (USD)"}


def system_prompt(level: str, layers: dict, docs: list[Doc], where: str = "dm", capped: bool = False,
                  cost: bool = False, country: str | None = None) -> str:
    parts = [f"<knowledge id=\"{d.id}\">\n{d.body}\n</knowledge>" for d in visible_docs(level, layers, docs, cost)]
    level_note = (layers.get("levels") or {}).get(level, {}).get("instructions", "")
    footer = f"\n\nThe answer is at level: {level}.\n{level_note}".rstrip()
    footer += "\n" + WHERE_NOTES.get(where, WHERE_NOTES["channel"])
    if capped:
        footer += ("\nThe asker has more access in a private DM. If the question needs more than this level allows, "
                   "say you can only share that in a DM, without hinting at the content.")
    if level != "owner" and not cost:
        footer += ("\nCost prices, markups, margins and contracts are locked at this level. Never hint at or estimate them; "
                   "point to the right flow and call `escalate` with kind decision.")
    if country in COUNTRY_NAMES:
        footer += (f"\nThe asker works in {COUNTRY_NAMES[country]}. Quote prices for that country only, unless they name "
                   "another country or ask for all countries.")
    else:
        footer += ("\nThe asker's country is unknown. If the question doesn't name a country, ask which one before quoting; "
                   "don't list every country's price.")
    return "\n\n".join(parts) + footer


# ---------- reply safety ----------
# A reply may only carry links to Foodics' own systems, Google Drive files (trimmed to the file id),
# or a link that appears word for word in our own knowledge or catalogue. Everything else is removed:
# prompt-injected text could otherwise hide data in a link to a site the attacker controls.
COMPANY_DOMAINS = ("foodics.com",)  # and its subdomains
COMPANY_HOSTS = ("foodics.slack.com", "foodics.lightning.force.com", "foodics.my.salesforce.com")
GOOGLE_FILE_HOSTS = ("docs.google.com", "drive.google.com")
_GOOGLE_FILE = re.compile(r"^/(?:(?:document|spreadsheets|presentation|file)/d/|drive/(?:u/\d+/)?folders/)[A-Za-z0-9_-]{10,}")
_URL = re.compile(r"https?://[^\s<>|()\[\]\"'`]+", re.I)
_ANGLE = re.compile(r"<([a-z][a-z0-9+.-]*:[^<>|]*)(?:\|([^<>]*))?>", re.I)  # Slack link markup, any scheme
_BARE = re.compile(r"(?<![\w@/.:-])((?:[a-z0-9-]+\.)+[a-z]{2,})(?=[/?#])[^\s<>|()\[\]]*", re.I)
_INVISIBLE = re.compile(r"[\u00ad\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff]")
_TRAIL = ".,;:!?)'\""


def _strip(url: str) -> str:
    return url.rstrip(_TRAIL)


def known_links(texts: list[str]) -> set[str]:
    """Every link that appears in our own knowledge and catalogue, exactly as written."""
    return {_strip(u) for t in texts for u in _URL.findall(t or "")}


def allowed_link(url: str, known: set[str]) -> str | None:
    """The link to keep (Drive links are trimmed to the file id), or None to remove it."""
    from urllib.parse import urlsplit
    url = _strip(url)
    if url in known:
        return url
    try:
        p = urlsplit(url)
        port = p.port
    except ValueError:
        return None
    host = (p.hostname or "").lower()
    if (p.scheme.lower() not in ("http", "https") or "@" in p.netloc or "\\" in url or port not in (None, 80, 443)
            or not host or not host.isascii()):
        return None
    if host in COMPANY_HOSTS or any(host == d or host.endswith("." + d) for d in COMPANY_DOMAINS):
        return url
    if host in GOOGLE_FILE_HOSTS:
        m = _GOOGLE_FILE.match(p.path)
        if m:
            return f"https://{host}{m.group(0)}"
    return None


def safe_reply(text: str, known: set[str]) -> str:
    """Remove unknown links (also in Slack <url|label> markup, other schemes and bare domains) and
    neutralise @channel/@here/@group and user pings."""
    text = _INVISIBLE.sub("", text or "")

    def angle(m: re.Match) -> str:
        target, label = m.group(1), m.group(2)
        keep = allowed_link(target, known) if re.match(r"https?://", target, re.I) else None
        if keep:
            return f"<{keep}|{label}>" if label else f"<{keep}>"
        return f"{label} [link removed]" if label else "[link removed]"

    text = _ANGLE.sub(angle, text)
    def bare_url(m: re.Match) -> str:
        url = m.group(0)
        return (allowed_link(url, known) or "[link removed]") + url[len(_strip(url)):]

    text = re.sub(r"(?<![<|])" + _URL.pattern, bare_url, text, flags=re.I)
    text = _BARE.sub(lambda m: m.group(0) if allowed_link("https://" + m.group(0), known) else "[link removed]", text)
    text = re.sub(r"<!(channel|here|everyone|subteam\^[A-Z0-9]+)[^>]*>", r"@\1", text)
    return re.sub(r"<@([UW][A-Z0-9]+)(?:\|[^>]*)?>", r"@\1", text)


SALES_TOOL_GUIDE = """
## Tools
- Call `brain_catalog` for every partner, line item, price and comparison. Never quote a price from memory.
- If the tool fails or returns nothing, say so plainly; do not invent the result.
- When the question needs a decision or operational detail you can't give, explain the flow, then call `escalate` once.
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
- When the question needs a person (a decision, or operational detail you don't have), explain the flow, then call `escalate` once.
"""
MAX_TOOL_TURNS = 8
LEVEL_RANK = {"sales": 0, "team": 1, "manager": 2, "owner": 3}


# Hard floors, whatever layers.yaml (a shared file) lists: tools that read private sources stay owner-only.
TOOL_MIN_LEVEL = {"salesforce_query": "owner", "drive_search": "owner", "drive_read": "owner",
                  "slack_read_channel": "owner", "learn": "owner", "sheets_read": "team", "read_slack_file": "team"}


def tools_for(level: str, layers: dict, tools: dict) -> dict:
    allowed = (layers.get("levels") or {}).get(level, {}).get("tools", [])
    rank = LEVEL_RANK.get(level, -1)
    return {k: v for k, v in tools.items()
            if k in allowed and rank >= LEVEL_RANK.get(TOOL_MIN_LEVEL.get(k, "sales"), 0)}


class Brain:
    def __init__(self, client: anthropic.Anthropic | None = None, tools: dict | None = None):
        self.client = client or anthropic.Anthropic()
        self.all_tools = tools or {}
        self.reload()

    def reload(self) -> None:
        self.docs = load_docs()
        self.layers = load_layers()
        catalog = [p.read_text(encoding="utf-8") for p in sorted(CATALOG_DIR.glob("*.json"))] if CATALOG_DIR.exists() else []
        self.known_links = known_links([d.body for d in self.docs] + catalog)

    def level_of(self, slack_user_id: str) -> str:
        return level_for(slack_user_id, self.layers)

    def ask(self, question: str, slack_user_id: str, history: list[dict] | None = None, *,
            level: str | None = None, where: str = "dm", ctx: dict | None = None) -> str:
        """`level` caps the answer (it can only lower the asker's own level); `where` says who reads it.
        `ctx` carries per-request data to tools (attached file ids) and back (hand-offs from `escalate`)."""
        ctx = {} if ctx is None else ctx
        own = level_for(slack_user_id, self.layers)
        level = own if level is None else (level if LEVEL_RANK.get(level, -1) <= LEVEL_RANK.get(own, -1) else own)
        if LEVEL_RANK.get(level, -1) < 0:
            level = "sales"
        capped = LEVEL_RANK.get(level, -1) < LEVEL_RANK.get(own, -1)
        # Cost and contracts only in a private DM, at the person's own level, for a cost grant.
        cost = (where == "dm" and not capped and cost_access(slack_user_id)
                and LEVEL_RANK.get(level, -1) >= LEVEL_RANK["manager"])
        tools = tools_for(level, self.layers, self.all_tools)
        guide = (SALES_TOOL_GUIDE if level == "sales" else TOOL_GUIDE) if tools else ""
        system = system_prompt(level, self.layers, self.docs, where=where, capped=capped, cost=cost,
                               country=(ctx or {}).get("country")) + guide
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
                        args["_ctx"] = ctx  # shared, so `escalate` can record hand-offs for the app
                    out = tool["fn"](**args) if tool else f"Tool '{u.name}' is not available at level {level}."
                    err = tool is None
                except Exception as exc:  # report the failure to the model instead of crashing
                    out, err = f"Tool error: {exc}", True
                results.append({"type": "tool_result", "tool_use_id": u.id, "content": out, "is_error": err})
            messages.append({"role": "user", "content": results})
        return "I needed too many lookups for this one. Please narrow the question."

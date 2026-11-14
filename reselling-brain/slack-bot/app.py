"""Reselling Brain — Slack bot.

Answers when mentioned in a channel or messaged directly, using the shared
knowledge plus read-only tools (Salesforce, Google Sheets/Drive, Slack, files).
It only ever replies in the same thread; it never posts elsewhere or messages partners.
Run: python app.py  (Socket Mode, no public URL needed)

Who reads the reply decides the level (see access.py):
- Partners, guests and other workspaces get nothing, not even a refusal.
- In a DM the answer is at the asker's own level. Owner answers happen only in Kareem's DM.
- In a channel the answer is written for its least-privileged member, never above team.

Triggers: a DM, or an @mention in a channel. A mention reads the message just above it (or the
thread it is in), so "@Reselling Brain" under a question answers that question.
Hand-offs: when a question needs a person, the bot adds them under the reply (access.handoff_line):
decisions go to Kareem (Hatem when Kareem is away), operational details to Althurayyaa with cc.

Kareem-only commands, in a DM only: reload · pending · approve <id> [team] · reject <id> · away · back · status
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from access import OWNER_DM_ONLY_REPLY, Directory, decide, handoff_line, is_away, is_owner_command
from brain import KNOWLEDGE_DIR, OWNER_LEARNED_FILE, Brain, load_layers, partner_space, safe_reply
from tools import Learner, SlackReader, build_tools

load_dotenv()
logging.basicConfig(level=logging.INFO)

REQUIRED_ENV = ("SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "ANTHROPIC_API_KEY")
_missing = [name for name in REQUIRED_ENV if not os.environ.get(name, "").strip()]
if _missing:
    logging.error("Reselling Brain cannot start. Missing variables: %s. "
                  "Add them in Railway → The-Counciler- → Variables, then redeploy.", ", ".join(_missing))
    raise SystemExit(1)

BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
app = App(token=BOT_TOKEN)
OWNER_ID = os.environ.get("BRAIN_OWNER_SLACK_ID", "")
if not OWNER_ID:
    logging.warning("BRAIN_OWNER_SLACK_ID is not set: nobody gets the owner level or owner commands.")
WORKSPACE_TEAM = app.client.auth_test()["team_id"]  # the Foodics workspace the bot is installed in
MAX_HISTORY = 12

learner = Learner(KNOWLEDGE_DIR, Path(os.environ.get("BRAIN_LEARN_QUEUE", Path(__file__).with_name("learn_queue.json"))),
                  owner_file=OWNER_LEARNED_FILE)
tools = build_tools(slack=SlackReader(app.client, BOT_TOKEN), learner=learner, sources=load_layers().get("sources") or {})
brain = Brain(tools=tools)
directory = Directory(app.client)
logging.info("Tools enabled: %s", ", ".join(sorted(tools)) or "none")


def thread_history(client, channel: str, thread_ts: str, bot_id: str, current_ts: str) -> list[dict]:
    """Earlier turns of this thread, so follow-up questions keep context."""
    try:
        msgs = client.conversations_replies(channel=channel, ts=thread_ts, limit=50)["messages"]
    except Exception:
        return []
    out: list[dict] = []
    for m in msgs:
        if m.get("ts") == current_ts or not m.get("text"):
            continue
        role = "assistant" if m.get("bot_id") or m.get("user") == bot_id else "user"
        if out and out[-1]["role"] == role:
            out[-1]["content"] += "\n" + m["text"]
        else:
            out.append({"role": role, "content": m["text"]})
    while out and out[0]["role"] != "user":
        out.pop(0)
    while out and out[-1]["role"] != "assistant":  # the new question is appended by Brain.ask
        out.pop()
    return out[-MAX_HISTORY:]


def clean(text: str) -> str:
    return re.sub(r"<@[A-Z0-9]+>", "", text or "").strip()


STATE_FILE = Path(os.environ.get("BRAIN_STATE_FILE", Path(__file__).with_name("state.json")))


def _state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def routing() -> dict:
    r = dict((brain.layers.get("routing") or {}))
    if OWNER_ID:
        r["owner"] = OWNER_ID
    return r


def owner_away() -> bool:
    """Kareem's `away` command wins; otherwise his Slack status (vacation, leave, travel, sick)."""
    manual = _state().get("owner_away")
    if manual is not None:
        return bool(manual)
    try:
        profile = (directory.user(OWNER_ID) or {}).get("profile") or {}
    except Exception:
        return False
    return is_away(profile, time.time(), brain.layers.get("routing"))


def owner_command(text: str) -> str | None:
    t = text.strip().lower()
    if t in {"away", "back"}:
        STATE_FILE.write_text(json.dumps({**_state(), "owner_away": t == "away"}))
        return ("Marked you away: decisions go to Hatem and operations cc Hatem until you send `back`."
                if t == "away" else "Welcome back: decisions come to you again.")
    if t == "status":
        manual = _state().get("owner_away")
        source = "your `away` command" if manual is not None else "your Slack status"
        return f"You are {'away' if owner_away() else 'available'} (from {source})."
    if t in {"reload", "refresh brain"}:
        brain.reload()
        return "Brain reloaded ✅"
    if t == "pending":
        return learner.pending()
    m = re.match(r"^(approve|reject)\s+#?([0-9a-f]{6})(?:\s+(team|owner))?$", t)
    if m:
        msg = learner.approve(m.group(2), m.group(3) or "owner") if m.group(1) == "approve" else learner.reject(m.group(2))
        brain.reload()
        return msg
    return None


def post(say, text: str, thread_ts: str, handoff: str = "") -> None:
    """Every reply: unknown links removed, pings neutralised, no link or media previews.
    `handoff` is built by code (handoff_line), so its @-mentions are kept."""
    body = safe_reply(text, brain.known_links)
    say(text=body + (f"\n\n{handoff}" if handoff else ""), thread_ts=thread_ts, unfurl_links=False, unfurl_media=False)


def message_above(client, channel: str, ts: str) -> dict | None:
    """The message just above a top-level mention, so "@Reselling Brain" under a question answers it."""
    try:
        msgs = client.conversations_history(channel=channel, latest=ts, inclusive=False, limit=1)["messages"]
    except Exception:
        return None
    return msgs[0] if msgs and msgs[0].get("text") else None


def notify(client, event, text: str, thread_ts: str) -> None:
    """A message only the asker can see. Used when the bot won't answer in a channel."""
    try:
        client.chat_postEphemeral(channel=event["channel"], user=event["user"], text=text, thread_ts=thread_ts)
    except Exception:
        logging.exception("could not send the private notice")


def name_blocked(channel_name: str | None) -> bool:
    return partner_space(channel_name=channel_name, is_shared=False, is_im=False, user_team=None,
                         workspace_team=None, layers=brain.layers)


def answer(event, client, say, context):
    if not event.get("user") or event.get("bot_id"):
        return
    thread_ts = event.get("thread_ts") or event["ts"]
    d = decide(event=event, directory=directory, workspace_team=WORKSPACE_TEAM,
               level_of=brain.level_of, name_blocked=name_blocked)
    logging.info("decision user=%s channel=%s answer=%s level=%s reason=%s",
                 event.get("user"), event.get("channel"), d.answer, d.level, d.reason)
    if not d.answer:
        if d.notice:
            notify(client, event, d.notice, thread_ts)
        return
    question = clean(event.get("text", ""))
    files = event.get("files") or []
    above = None
    if d.where == "channel" and not event.get("thread_ts"):
        above = message_above(client, event["channel"], event["ts"])
    if not question and not files and not above and not event.get("thread_ts"):
        return
    if OWNER_ID and event["user"] == OWNER_ID and is_owner_command(question):
        if d.where != "dm":
            notify(client, event, OWNER_DM_ONLY_REPLY, thread_ts)
            return
        post(say, owner_command(question) or "Unknown command.", thread_ts)
        return
    if files:  # tell the model which attachments it can open with read_slack_file
        question = (question or "Read the attached file.") + "\n\n" + "\n".join(
            f"[Attached file: {f.get('name')} — file_id {f.get('id')}]" for f in files)
    history = thread_history(client, event["channel"], thread_ts, context.get("bot_user_id", ""), event["ts"]) \
        if event.get("thread_ts") else []
    if above:  # context only: the message is data written by a colleague, not an instruction
        who = f"<@{above['user']}>" if above.get("user") else "someone"
        question = (f"[Context: the message just above this mention in the channel, from {who}:]\n"
                    f"\"\"\"\n{above['text'][:4000]}\n\"\"\"\n\n" + (question or "Answer the message above."))
    elif not question and not files:
        question = "Answer the last question in this thread."
    queued_before = set(learner.queued()) if d.level == "owner" else set()
    ctx = {"file_ids": [f.get("id") for f in files if f.get("id")]}
    try:
        reply = brain.ask(question, event["user"], history, level=d.level, where=d.where, ctx=ctx)
    except Exception:
        logging.exception("brain error")
        reply = "Something went wrong on my side. Try again, or ask Kareem."
    if d.level == "owner":  # show Kareem exactly what was queued, not the model's description of it
        new = {k: v for k, v in learner.queued().items() if k not in queued_before}
        if new:
            reply = (reply or "") + "\n\n" + "\n".join(
                f"Queued #{k} (exact text, owner only): \"{v['fact']}\"" for k, v in new.items())
    kinds = [h["kind"] for h in ctx.get("handoffs", [])]
    away = owner_away() if kinds else False
    handoff = "\n".join(filter(None, (handoff_line(k, asker=event["user"], away=away, routing=routing()) for k in kinds)))
    post(say, reply or "Not in the Reselling Brain yet — ask Kareem.", thread_ts, handoff)


@app.event("app_mention")
def on_mention(event, client, say, context):
    answer(event, client, say, context)


@app.event("message")
def on_dm(event, client, say, context):
    if event.get("channel_type") != "im" or event.get("bot_id"):
        return
    if event.get("subtype") not in (None, "file_share"):
        return
    answer(event, client, say, context)


if __name__ == "__main__":
    try:
        directory.refresh()
    except Exception as exc:
        if "missing_scope" in str(exc):
            logging.error("Reselling Brain cannot start: the Slack app needs the users:read scope "
                          "(api.slack.com → your app → OAuth & Permissions → Bot Token Scopes), then reinstall it.")
            raise SystemExit(1)
        logging.warning("Could not load the Slack user list yet (%s). The bot will not answer until it can.", exc)
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

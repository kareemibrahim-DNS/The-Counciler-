"""Reselling Brain — Slack bot.

Answers when mentioned in a channel or messaged directly, using the shared
knowledge plus read-only tools (Salesforce, Google Sheets/Drive, Slack, files).
It only ever replies in the same thread; it never posts elsewhere or messages partners.
Run: python app.py  (Socket Mode, no public URL needed)

Kareem-only commands: reload · pending · approve <id> · reject <id>
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from brain import KNOWLEDGE_DIR, PARTNER_SPACE_REPLY, Brain, load_layers, partner_space
from tools import Learner, SlackReader, build_tools

load_dotenv()
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
app = App(token=BOT_TOKEN)
OWNER_ID = os.environ.get("BRAIN_OWNER_SLACK_ID", "")
MAX_HISTORY = 12

learner = Learner(KNOWLEDGE_DIR, Path(os.environ.get("BRAIN_LEARN_QUEUE", Path(__file__).with_name("learn_queue.json"))))
tools = build_tools(slack=SlackReader(app.client, BOT_TOKEN), learner=learner, sources=load_layers().get("sources") or {})
brain = Brain(tools=tools)
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


def owner_command(text: str) -> str | None:
    t = text.strip().lower()
    if t in {"reload", "refresh brain"}:
        brain.reload()
        return "Brain reloaded ✅"
    if t == "pending":
        return learner.pending()
    m = re.match(r"^(approve|reject)\s+#?([0-9a-f]{6})$", t)
    if m:
        msg = learner.approve(m.group(2)) if m.group(1) == "approve" else learner.reject(m.group(2))
        brain.reload()
        return msg
    return None


def in_partner_space(event, client) -> bool:
    is_im = event.get("channel_type") == "im"
    name, shared = None, False
    if not is_im:
        try:
            ch = client.conversations_info(channel=event["channel"])["channel"]
            name, shared = ch.get("name"), bool(ch.get("is_ext_shared") or ch.get("is_shared"))
        except Exception:
            return True  # fail closed: if we can't tell who can read the channel, don't answer there
    return partner_space(channel_name=name, is_shared=shared, is_im=is_im, user_team=event.get("user_team"),
                         workspace_team=event.get("team"), layers=brain.layers)


def answer(event, client, say, context):
    thread_ts = event.get("thread_ts") or event["ts"]
    if in_partner_space(event, client):
        say(text=PARTNER_SPACE_REPLY, thread_ts=thread_ts)
        return
    question = clean(event.get("text", ""))
    files = event.get("files") or []
    if files:  # tell the model which attachments it can open with read_slack_file
        question += "\n\n" + "\n".join(f"[Attached file: {f.get('name')} — file_id {f.get('id')}]" for f in files)
    if not question:
        return
    if event.get("user") == OWNER_ID:
        reply = owner_command(question)
        if reply:
            say(text=reply, thread_ts=thread_ts)
            return
    history = thread_history(client, event["channel"], thread_ts, context.get("bot_user_id", ""), event["ts"]) \
        if event.get("thread_ts") else []
    try:
        reply = brain.ask(question, event.get("user", ""), history)
    except Exception:
        logging.exception("brain error")
        reply = "Something went wrong on my side. Try again, or ask Kareem."
    say(text=reply or "Not in the Reselling Brain yet — ask Kareem.", thread_ts=thread_ts)


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
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

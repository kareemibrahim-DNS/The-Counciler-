"""Brain Watch: what the bot couldn't answer, and where Kareem, Hatem or Althurayyaa stepped in.

Everything is kept in one JSON file on the private `/data` volume (`BRAIN_WATCH_FILE`), never in git.
Only Kareem sees it, with DM commands (see app.py):
  review          scan the logged threads again, then show corrections, unanswered questions and notes
  note <text>     add something of your own to the log
  teach <id>      turn a correction (or a note) into a learn proposal (`approve <id>` as usual)
  dismiss <id>    drop an item from the review (it was not a correction, or it's handled)
  digest          the 2-week digest: insights (answers, response time, most asked, who asks most) + the review

What counts:
- "Unanswered": the bot answered with a hand-off, said a part is locked, said it isn't in the brain yet, or failed.
- "Stepped in": in a channel thread where the bot replied, one of the watched people (Kareem, Hatem,
  Althurayyaa, from `routing` in layers.yaml) wrote after the bot's reply, and they weren't the asker and
  weren't asking the bot again. Kareem decides in `review` whether it was a real correction.
Uses only scopes the bot already has (channels:history, groups:history): no new Slack events, no reinstall.
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid
from collections import Counter
from pathlib import Path

WATCH_FILE = Path(os.environ.get("BRAIN_WATCH_FILE", Path(__file__).with_name("watch.json")))
# The 2-week digest DM (Kareem, 16 Nov 2026): every other Sunday at 11:30 Riyadh time (UTC+3, no DST),
# starting Sunday 22 Nov 2026. A missed slot (bot down) is sent once when it comes back, the same day only.
DIGEST_ANCHOR = (2026, 11, 22)
DIGEST_AT = (11, 30)
RIYADH = 3 * 3600
KEEP_DAYS = 60          # older answers are dropped from the file
SCAN_DAYS = 14          # threads younger than this are re-read on `review`
SCAN_LIMIT = 80         # at most this many threads per `review` (Slack rate limits)
NO_ANSWER = re.compile(r"can't answer (this|that)?\s*(part)?\s*here|not in the reselling brain yet|"
                       r"something went wrong on my side|i don't (have|know)|لا أستطيع|مش عارف", re.I)


def _short(text: str, n: int = 220) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= n else text[: n - 1] + "…"


def _topic(question: str) -> str:
    """A rough key so the same question asked in different words still groups together."""
    words = re.findall(r"[\w؀-ۿ]+", (question or "").lower())
    stop = {"the", "a", "an", "is", "are", "what", "how", "do", "does", "we", "i", "to", "for", "of", "in", "on",
            "can", "you", "me", "please", "and", "or", "with", "it", "this", "that", "our", "my", "be", "any", "there"}
    keep = [w for w in words if w not in stop and not w.isdigit()]
    return " ".join(sorted(set(keep[:8]))) or _short(question, 40).lower()


def digest_slot(now: float) -> str:
    """Today's digest slot ('YYYY-MM-DD') if a digest is due at `now`, else ''."""
    import datetime as dt
    local = dt.datetime.fromtimestamp(now + RIYADH, dt.timezone.utc).replace(tzinfo=None)
    days = (local.date() - dt.date(*DIGEST_ANCHOR)).days
    if days < 0 or days % 14 or (local.hour, local.minute) < DIGEST_AT:
        return ""
    return local.date().isoformat()


class Watch:
    def __init__(self, path: Path = WATCH_FILE):
        self.path = path

    # ---------- storage ----------
    def _load(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        data.setdefault("answers", {})
        data.setdefault("notes", {})
        return data

    def _save(self, data: dict) -> None:
        cutoff = time.time() - KEEP_DAYS * 86400
        data["answers"] = {k: v for k, v in data["answers"].items() if v.get("at", 0) >= cutoff}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, self.path)  # atomic

    # ---------- writing ----------
    def record(self, *, channel: str, thread_ts: str, reply_ts: str, asker: str, question: str, reply: str,
               handoffs: list[str], where: str, link: str = "", error: bool = False, secs: float | None = None,
               level: str = "", team: str = "") -> str:
        """Log one bot answer. Never raises: the watch must not break a reply."""
        try:
            data = self._load()
            rid = uuid.uuid4().hex[:6]
            data["answers"][rid] = {
                "at": time.time(), "channel": channel, "thread_ts": thread_ts, "reply_ts": reply_ts or "",
                "asker": asker, "where": where, "question": _short(question, 600), "reply": _short(reply, 600),
                "handoffs": handoffs, "link": link,
                "unanswered": bool(error or handoffs or NO_ANSWER.search(reply or "")),
                "stepped_in": [], "dismissed": False,
                "secs": round(secs, 1) if secs is not None else None, "level": level, "team": _short(team, 60),
            }
            self._save(data)
            return rid
        except Exception:
            return ""

    def note(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return "Write the note after `note`, for example: `note Grubtech quotes need the branch count first`."
        data = self._load()
        nid = uuid.uuid4().hex[:6]
        data["notes"][nid] = {"at": time.time(), "text": text[:2000], "dismissed": False}
        self._save(data)
        return f"Noted #{nid}. It shows in `review`; send `teach {nid}` to turn it into a fact for the brain."

    def dismiss(self, rid: str) -> str:
        data = self._load()
        item = data["answers"].get(rid) or data["notes"].get(rid)
        if not item:
            return f"No item #{rid}."
        item["dismissed"] = True
        self._save(data)
        return f"Dismissed #{rid}."

    def teach_text(self, rid: str) -> str | None:
        """The text to queue as a learn proposal: what the person wrote, with the question for context."""
        data = self._load()
        if rid in data["notes"]:
            return data["notes"][rid]["text"]
        a = data["answers"].get(rid)
        if not a or not a["stepped_in"]:
            return None
        fix = " / ".join(s["text"] for s in a["stepped_in"])
        return f"Q: {a['question']} -> correct answer: {fix}"

    def claim_digest(self, now: float | None = None) -> str:
        """The due slot, marked as sent so it goes out once (survives restarts on /data); '' if none is due."""
        slot = digest_slot(time.time() if now is None else now)
        if not slot:
            return ""
        data = self._load()
        if data.get("digest_sent") == slot:
            return ""
        data["digest_sent"] = slot
        self._save(data)
        return slot

    # ---------- scanning ----------
    def scan(self, client, *, watched: dict[str, str], bot_ids: set[str]) -> int:
        """Re-read recent channel threads the bot answered; return how many threads were read."""
        data, read = self._load(), 0
        cutoff = time.time() - SCAN_DAYS * 86400
        recent = sorted(((k, a) for k, a in data["answers"].items()
                         if a["where"] != "dm" and a.get("reply_ts") and a["at"] >= cutoff),
                        key=lambda kv: kv[1]["at"], reverse=True)
        by_thread: dict[tuple, list] = {}
        for k, a in recent:
            by_thread.setdefault((a["channel"], a["thread_ts"]), []).append((k, a))
        for (channel, thread_ts), items in list(by_thread.items())[:SCAN_LIMIT]:
            try:
                msgs = client.conversations_replies(channel=channel, ts=thread_ts, limit=200)["messages"]
            except Exception:
                continue
            read += 1
            for k, a in items:
                later = [m for m in msgs if float(m.get("ts", 0)) > float(a["reply_ts"])]
                nxt = next((float(m["ts"]) for m in later if m.get("bot_id") in bot_ids or m.get("user") in bot_ids), None)
                seen = {s["ts"] for s in a["stepped_in"]}
                for m in later:
                    if nxt is not None and float(m["ts"]) >= nxt:
                        break  # after the bot's next reply it belongs to that answer
                    user = m.get("user")
                    if user not in watched or user == a["asker"] or m["ts"] in seen:
                        continue
                    if any(f"<@{b}>" in (m.get("text") or "") for b in bot_ids):
                        continue  # asking the bot again, not correcting it
                    a["stepped_in"].append({"by": watched[user], "user": user, "ts": m["ts"],
                                            "text": _short(m.get("text"), 600)})
        self._save(data)
        return read

    # ---------- insights (the 2-week digest) ----------
    def insights(self, *, days: int = 14, names: dict[str, str] | None = None) -> str:
        names = names or {}
        since = time.time() - days * 86400
        rows = [a for a in self._load()["answers"].values() if a.get("at", 0) >= since]
        out = [f"*Insights, last {days} days*"]
        if not rows:
            return out[0] + "\n   No answers logged yet."
        secs = sorted(a["secs"] for a in rows if a.get("secs") is not None)
        unanswered = sum(1 for a in rows if a["unanswered"])
        stepped = sum(1 for a in rows if a["stepped_in"])
        out.append(f"   {len(rows)} answers to {len({a['asker'] for a in rows})} people · "
                   f"{unanswered} without a clear answer ({round(100 * unanswered / len(rows))}%) · "
                   f"{stepped} where someone stepped in")
        if secs:
            p90 = secs[min(len(secs) - 1, int(len(secs) * 0.9))]
            out.append(f"   Response time: median {secs[len(secs) // 2]:.0f}s, slowest 10% over {p90:.0f}s")
        where = Counter(a["where"] for a in rows)
        out.append("   Where: " + ", ".join(f"{k} {v}" for k, v in where.most_common()))
        teams = Counter((a.get("team") or a.get("level") or "unknown") for a in rows)
        out.append("   Who asks most (Slack title or level): " + ", ".join(f"{k} {v}" for k, v in teams.most_common(6)))
        people = Counter(a["asker"] for a in rows)
        out.append("   Top askers: " + ", ".join(f"{names.get(u, '<@' + u + '>')} {v}" for u, v in people.most_common(5)))
        topics = Counter(_topic(a["question"]) for a in rows)
        sample = {}
        for a in sorted(rows, key=lambda a: a["at"], reverse=True):
            sample.setdefault(_topic(a["question"]), a)
        out.append("   Most asked:")
        for t, n in topics.most_common(8):
            out.append(f"      {n}× {_short(sample[t]['question'], 140)}")
        return "\n".join(out)

    # ---------- the report ----------
    def report(self, *, limit: int = 15) -> str:
        data = self._load()
        answers = {k: a for k, a in data["answers"].items() if not a.get("dismissed")}
        fixes = sorted(((k, a) for k, a in answers.items() if a["stepped_in"]), key=lambda kv: kv[1]["at"], reverse=True)
        open_q = [a for a in answers.values() if a["unanswered"] and not a["stepped_in"]]
        notes = sorted(((k, n) for k, n in data["notes"].items() if not n.get("dismissed")),
                       key=lambda kv: kv[1]["at"], reverse=True)
        out = [f"*Brain Watch* (last {KEEP_DAYS} days, {len(answers)} answers logged)"]

        out.append(f"\n*1. Someone stepped in after the bot ({len(fixes)})*")
        for k, a in fixes[:limit]:
            who = ", ".join(sorted({s["by"] for s in a["stepped_in"]}))
            out.append(f"#{k} · {time.strftime('%d %b', time.gmtime(a['at']))} · {who}"
                       + (f" · <{a['link']}|thread>" if a.get("link") else ""))
            out.append(f"   Q: {_short(a['question'], 160)}")
            out.append(f"   Bot: {_short(a['reply'], 160)}")
            for s in a["stepped_in"][:2]:
                out.append(f"   {s['by']}: {_short(s['text'], 200)}")
        if not fixes:
            out.append("   None yet.")

        groups = Counter(_topic(a["question"]) for a in open_q)
        sample = {}
        for a in sorted(open_q, key=lambda a: a["at"], reverse=True):
            sample.setdefault(_topic(a["question"]), a)
        out.append(f"\n*2. Asked without an answer or a clear answer ({len(open_q)})*, most asked first")
        for topic, n in groups.most_common(limit):
            a = sample[topic]
            why = "hand-off: " + ", ".join(a["handoffs"]) if a["handoffs"] else "no clear answer"
            out.append(f"   {n}× {_short(a['question'], 160)} ({why})"
                       + (f" · <{a['link']}|latest>" if a.get("link") else ""))
        if not open_q:
            out.append("   None.")

        out.append(f"\n*3. Your notes ({len(notes)})*")
        for k, n in notes[:limit]:
            out.append(f"#{k} · {time.strftime('%d %b', time.gmtime(n['at']))} · {_short(n['text'], 240)}")
        if not notes:
            out.append("   None. Add one with `note <text>`.")

        out.append("\n`teach <id>` turns a correction or note into a fact for the brain (then `approve <id>` as usual) · "
                   "`dismiss <id>` drops it from this list")
        return "\n".join(out)

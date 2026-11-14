"""Who is asking, and who can read the reply.

The bot decides two things before it answers:
1. Is the asker a Foodics full member? Guests, Slack Connect users and anyone the bot
   cannot identify are partners or outsiders: they get nothing, not even a refusal.
2. Who can read the reply? In a DM, only the asker. In a private channel, every member, so
   the answer is written for the least-privileged member and never above team level. A public
   channel can be opened and searched by every full member, so it always gets the sales level.
   Owner-level answers only ever happen in Kareem's DM.

Every check fails closed: if Slack cannot tell us who is asking or who can read the
channel, the bot does not answer there.
"""
from __future__ import annotations

import logging
import re
import threading
import time
from dataclasses import dataclass
from typing import Callable

LEVEL_ORDER = {"sales": 0, "team": 1, "owner": 2}
CHANNEL_MAX_LEVEL = "team"  # owner answers never leave Kareem's DM
SHARED_FLAGS = ("is_ext_shared", "is_shared", "is_org_shared", "is_pending_ext_shared", "pending_shared")

PARTNER_SPACE_REPLY = ("I don't answer in channels that partners or other workspaces can read. "
                       "Ask me in a DM, or in an internal Foodics channel.")
CANNOT_CHECK_REPLY = "I can't check who can read this channel, so I won't answer here. Ask me in a DM."
OWNER_DM_ONLY_REPLY = "Send owner commands to me in a DM."
_OWNER_COMMAND = re.compile(r"^(reload|refresh brain|pending|(approve|reject)\s+#?[0-9a-f]{6}(\s+(team|owner))?)$")


def is_owner_command(text: str) -> bool:
    return bool(_OWNER_COMMAND.match((text or "").strip().lower()))


def rank(level: str) -> int:
    """Unknown levels rank below sales, so they are treated as the most limited layer."""
    return LEVEL_ORDER.get(level, -1)


def lower(a: str, b: str) -> str:
    low = a if rank(a) <= rank(b) else b
    return low if rank(low) >= 0 else "sales"


def is_outsider(user: dict | None, workspace_team: str) -> bool:
    """True for guests, Slack Connect users, deleted or unknown users, and other workspaces."""
    if not user or user.get("deleted"):
        return True
    if user.get("is_restricted") or user.get("is_ultra_restricted") or user.get("is_stranger"):
        return True
    teams = {user.get("team_id")} | set((user.get("enterprise_user") or {}).get("teams") or [])
    return not workspace_team or workspace_team not in teams


def channel_level(member_levels: list[str]) -> str:
    """A channel reply is written for its least-privileged reader, and never above team."""
    if not member_levels:
        return "sales"
    low = min(member_levels, key=rank)
    return lower(low, CHANNEL_MAX_LEVEL)


def is_shared_channel(ch: dict) -> bool:
    return any(ch.get(k) for k in SHARED_FLAGS)


@dataclass(frozen=True)
class Decision:
    answer: bool
    level: str = "sales"
    where: str = "dm"            # "dm" or "channel"
    notice: str | None = None    # shown only to the asker (ephemeral) when the bot won't answer
    reason: str = ""


class Directory:
    """Cached Slack user list and channel members (needs the users:read scope)."""

    def __init__(self, client, users_ttl: float = 60, members_ttl: float = 0, clock: Callable[[], float] = time.time):
        self.client, self.users_ttl, self.members_ttl, self.clock = client, users_ttl, members_ttl, clock
        self._users: dict[str, dict] = {}
        self._loaded_at = float("-inf")
        self._members: dict[str, tuple[float, list[str]]] = {}
        self._lock = threading.Lock()

    def refresh(self) -> None:
        users, cursor = {}, None
        while True:
            r = self.client.users_list(limit=1000, cursor=cursor)
            users.update({u["id"]: u for u in r["members"]})
            cursor = (r.get("response_metadata") or {}).get("next_cursor")
            if not cursor:
                break
        self._users, self._loaded_at = users, self.clock()

    def user(self, uid: str) -> dict | None:
        if not uid:
            return None
        with self._lock:
            age = self.clock() - self._loaded_at
            if age > self.users_ttl or (uid not in self._users and age > 60):
                self.refresh()
            u = self._users.get(uid)
            if u is None:  # people from other workspaces are not in users.list
                u = self.client.users_info(user=uid)["user"]
                self._users[uid] = u
            return u

    def members(self, channel: str) -> list[str]:
        hit = self._members.get(channel)
        if hit and self.clock() - hit[0] < self.members_ttl:
            return hit[1]
        ids, cursor = [], None
        while True:
            r = self.client.conversations_members(channel=channel, limit=1000, cursor=cursor)
            ids += r["members"]
            cursor = (r.get("response_metadata") or {}).get("next_cursor")
            if not cursor:
                break
        self._members[channel] = (self.clock(), ids)
        return ids

    def channel(self, channel: str) -> dict:
        return self.client.conversations_info(channel=channel)["channel"]


def is_dm(event: dict) -> bool:
    return event.get("channel_type") == "im" and str(event.get("channel", "")).startswith("D")


def decide(*, event: dict, directory: Directory, workspace_team: str, level_of: Callable[[str], str],
           name_blocked: Callable[[str | None], bool]) -> Decision:
    """Whether to answer, at which level, and where. See the module docstring."""
    uid = event.get("user") or ""
    try:
        asker = directory.user(uid)
    except Exception as exc:
        logging.error("Cannot look up the asker %s (%s). Not answering. Does the app have the users:read scope?", uid, exc)
        return Decision(False, reason="asker-unknown")
    if not asker or asker.get("is_bot") or is_outsider(asker, workspace_team):
        return Decision(False, reason="outsider")  # partners get nothing, not even a refusal
    if is_dm(event):
        return Decision(True, level=level_of(uid), where="dm", reason="dm")
    try:
        ch = directory.channel(event["channel"])
        if ch.get("is_im") or ch.get("is_mpim") or is_shared_channel(ch) or name_blocked(ch.get("name")):
            return Decision(False, notice=PARTNER_SPACE_REPLY, reason="partner-channel")
        levels = []
        for m in directory.members(event["channel"]):
            u = directory.user(m)
            if u and u.get("deleted") and (u.get("is_bot") or not is_outsider({**u, "deleted": False}, workspace_team)):
                continue  # deactivated staff and removed apps can't read; a deactivated guest still blocks
            if is_outsider(u, workspace_team):
                return Decision(False, notice=PARTNER_SPACE_REPLY, reason="outsider-member")
            if not u.get("is_bot"):
                levels.append(level_of(m))
        if ch.get("is_private") is not True:
            levels.append("sales")  # any full member can preview and search a public channel
    except Exception as exc:
        logging.error("Cannot check who can read %s (%s). Not answering there.", event.get("channel"), exc)
        return Decision(False, notice=CANNOT_CHECK_REPLY, reason="channel-unknown")
    level = lower(level_of(uid), channel_level(levels + [level_of(uid)]))
    return Decision(True, level=level, where="channel", reason="channel")

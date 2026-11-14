"""Offline tests of app.py's wiring: every Slack Web API call is faked, Claude is faked.

Run: python -m unittest test_app   (the Docker build runs it together with test_brain)
"""
import importlib
import os
import tempfile
import unittest
from types import SimpleNamespace as NS
from unittest import mock

from access import PARTNER_SPACE_REPLY
from slack_sdk.web.base_client import BaseClient
from slack_sdk.web.slack_response import SlackResponse

T = "TFOODICS"
OWNER, TEAM, SALES, GUEST, BOT = "UK", "U0BQKNQNF89", "US", "UG", "UBOT"
USERS = {OWNER: {"id": OWNER, "team_id": T}, TEAM: {"id": TEAM, "team_id": T}, SALES: {"id": SALES, "team_id": T},
         GUEST: {"id": GUEST, "team_id": T, "is_restricted": True}, BOT: {"id": BOT, "team_id": T, "is_bot": True}}
CHANNELS = {"CPRIV": ({"name": "partnerships-internal", "is_private": True}, [OWNER, TEAM, BOT]),
            "CPUB": ({"name": "reseller-hub", "is_private": False}, [OWNER, TEAM, BOT]),
            "CSHARED": ({"name": "launch", "is_private": True, "is_ext_shared": True}, [OWNER, BOT]),
            "CGUEST": ({"name": "grubtech-onboarding", "is_private": True}, [OWNER, GUEST, BOT])}
CALLS = []


def fake_api_call(self, api_method, **kw):
    args = kw.get("params") or kw.get("json") or kw.get("data") or {}
    CALLS.append((api_method, dict(args)))
    if api_method == "auth.test":
        data = {"team_id": T, "user_id": BOT, "bot_id": "B1"}
    elif api_method == "users.list":
        data = {"members": list(USERS.values()), "response_metadata": {"next_cursor": ""}}
    elif api_method == "users.info":
        raise RuntimeError("user_not_found")
    elif api_method == "conversations.info":
        data = {"channel": CHANNELS[args["channel"]][0]}
    elif api_method == "conversations.members":
        data = {"members": CHANNELS[args["channel"]][1], "response_metadata": {"next_cursor": ""}}
    elif api_method == "conversations.replies":
        data = {"messages": []}
    else:
        data = {}
    return SlackResponse(client=self, http_verb="POST", api_url=api_method, req_args={}, data={"ok": True, **data},
                         headers={}, status_code=200)


class FakeClaude:
    def __init__(self, script):
        self.script, self.calls = list(script), []
        self.messages = self

    def create(self, **kw):
        self.calls.append(kw)
        return self.script.pop(0)


def text(t):
    return NS(content=[NS(type="text", text=t)], stop_reason="end_turn")


def tool_call(name, args):
    return NS(content=[NS(type="tool_use", id="t1", name=name, input=args,
                          model_dump=lambda: {"type": "tool_use", "id": "t1", "name": name, "input": args})],
              stop_reason="tool_use")


app = None
_patches = []


def setUpModule():
    global app
    tmp = tempfile.mkdtemp()
    _patches.append(mock.patch.dict(os.environ, {
        "SLACK_BOT_TOKEN": "xoxb-test", "SLACK_APP_TOKEN": "xapp-test", "ANTHROPIC_API_KEY": "sk-test",
        "BRAIN_OWNER_SLACK_ID": OWNER, "BRAIN_LEARN_QUEUE": os.path.join(tmp, "q.json")}))
    _patches.append(mock.patch.object(BaseClient, "api_call", fake_api_call))
    for p in _patches:
        p.start()
    app = importlib.import_module("app")


def tearDownModule():
    for p in reversed(_patches):
        p.stop()


class AppWiring(unittest.TestCase):
    def run_event(self, user, channel, text_="", script=None, **extra):
        CALLS.clear()
        said = []
        app.brain.client = FakeClaude(script or [text("ok")])
        event = {"user": user, "channel": channel, "text": text_, "ts": "1.1", **extra}
        if channel.startswith("D"):
            event.setdefault("channel_type", "im")
        app.answer(event, app.app.client, lambda **k: said.append(k), {"bot_user_id": BOT})
        ephemeral = [a for m, a in CALLS if m == "chat.postEphemeral"]
        for s in said:
            self.assertIs(s.get("unfurl_links"), False)
            self.assertIs(s.get("unfurl_media"), False)
            self.assertEqual(s.get("thread_ts"), "1.1")
        return said, ephemeral

    def level(self):
        sys = app.brain.client.calls[0]["system"][0]["text"]
        return sys.split("The answer is at level: ")[1].split(".")[0]

    def test_owner_dm_is_owner_level_and_the_reply_is_cleaned(self):
        said, eph = self.run_event(OWNER, "DK", "markup?", [text("See https://evil.example/p?d=1 <!channel>")])
        self.assertEqual(self.level(), "owner")
        self.assertEqual(len(said), 1)
        self.assertNotIn("evil.example", said[0]["text"])
        self.assertNotIn("<!channel>", said[0]["text"])
        self.assertEqual(eph, [])

    def test_private_team_channel_is_team_and_public_channel_is_sales(self):
        self.run_event(OWNER, "CPRIV", "<@UBOT> discount band?")
        self.assertEqual(self.level(), "team")
        self.run_event(TEAM, "CPUB", "<@UBOT> discount band?")
        self.assertEqual(self.level(), "sales")

    def test_partner_channels_get_only_a_private_note_to_the_asker(self):
        for ch in ["CSHARED", "CGUEST"]:
            said, eph = self.run_event(OWNER, ch, "<@UBOT> hi")
            self.assertEqual(said, [], ch)
            self.assertEqual([(e["user"], e["text"]) for e in eph], [(OWNER, PARTNER_SPACE_REPLY)], ch)
            self.assertEqual(app.brain.client.calls, [], ch)

    def test_a_guest_gets_nothing_at_all(self):
        said, eph = self.run_event(GUEST, "DG", "prices?")
        self.assertEqual((said, eph, app.brain.client.calls), ([], [], []))

    def test_owner_commands_only_in_the_dm(self):
        said, eph = self.run_event(OWNER, "CPRIV", "<@UBOT> pending")
        self.assertEqual(said, [])
        self.assertEqual([e["text"] for e in eph], [app.OWNER_DM_ONLY_REPLY])
        said, _ = self.run_event(OWNER, "DK", "pending")
        self.assertEqual(len(said), 1)
        self.assertEqual(app.brain.client.calls, [], "commands never reach the model")

    def test_a_file_with_no_text_is_answered_with_that_file_only(self):
        seen = {}

        def spy(question, user, history=None, **kw):
            seen.update(kw, question=question)
            return "read it"
        with mock.patch.object(app.brain, "ask", spy):
            said, _ = self.run_event(TEAM, "DT", "", files=[{"id": "F1", "name": "quote.pdf"}], subtype="file_share")
        self.assertEqual(seen["ctx"], {"file_ids": ["F1"]})
        self.assertIn("file_id F1", seen["question"])
        self.assertEqual(len(said), 1)

    def test_kareem_sees_the_exact_queued_fact_not_the_models_summary(self):
        script = [tool_call("learn", {"fact": "Grubtech markup is 42%"}), text("I queued a harmless SLA note.")]
        said, _ = self.run_event(OWNER, "DK", "remember this", script)
        self.assertIn('(exact text, owner only): "Grubtech markup is 42%"', said[0]["text"])


if __name__ == "__main__":
    unittest.main()

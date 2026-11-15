"""Builds the common-layer Claude skill (for @Claude in Slack) from the same knowledge and catalogue the bot uses.

    python build_sales_skill.py            # rewrites ../sales-skill/reselling-brain-sales/references/catalog.md
    python build_sales_skill.py --zip DIR  # also writes DIR/reselling-brain-sales.zip to upload in claude.ai

The skill gets exactly the bot's common layer: the `base` knowledge files and Catalog.lookup at level
"sales" (resellers, list prices, quote structure, comparisons, merchant fit, forms). No discount rules,
cost, contracts, contacts, trackers, partner Slack channels or team notes. Claude in Slack gives everyone
the same knowledge, so nothing above the common layer may go in it.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import re

import brain
import tools

SKILL_DIR = Path(__file__).resolve().parent.parent / "sales-skill" / "reselling-brain-sales"
CURRENCIES = {"SAR": "KSA (SAR)", "AED": "UAE (AED)", "KWD": "Kuwait (KWD)", "JOD": "Jordan (JOD)",
              "EGP": "Egypt (EGP)", "USD": "International (USD)"}


def catalog_markdown(cat: tools.Catalog) -> str:
    lines = ["# Reseller catalogue: available resellers, list prices, quote structure", "",
             "Source: Salesforce Standard Price Book + \"USD 1 – International\", refreshed 14 Nov 2026. LIST (selling) prices only.",
             "A blank price means the line is not sold in that country. Never convert between currencies.", "", "## Categories"]
    cats = json.loads(cat.lookup(level="sales"))["categories"]
    lines += [f"- **{c['name']}**: {', '.join(c['partners'])}" for c in cats] + [""]
    for c in cats:
        side = json.loads(cat.lookup(category=c["id"], level="sales"))
        lines += [f"# Category: {c['name']}", "", f"How to choose: {side['how_to_choose']}", ""]
        for p in c["partners"]:
            if p not in cat.partners:
                continue
            d = json.loads(cat.lookup(partner=p, level="sales"))
            lines.append(f"## {d['partner']}" + (" — INACTIVE, do not quote" if d["inactive"] else ""))
            lines += [f"- Category: {d['category']}", f"- What it is: {d['overview']}",
                      f"- Best for: {d['best_for']}", f"- Edge: {d['edge']}",
                      f"- Licensing unit: {d['licensing_unit']}", f"- Countries: {d['countries']}"]
            if d.get("watch_out"):
                lines.append(f"- Watch out: {d['watch_out']}")
            lines.append(f"- Submit deals with: {d['submission_form']} (KSA approval form: {d['ksa_approval_form']})")
            if d["quote_rules"]:
                lines += ["- Quote structure:"] + [f"  - {r}" for r in d["quote_rules"]]
            lines += ["", "| Line item (exact Salesforce name) | Type | Billing | " + " | ".join(CURRENCIES.values()) + " |",
                      "|---|---|---|" + "---|" * len(CURRENCIES)]
            for l in d["line_items"]:
                pr = l.get("prices", {})
                name = l["name"] + (f" ⚠ {l['warning']}" if l.get("warning") else "")
                lines.append(f"| {name} | {l['type']} | {l['billing']} | " +
                             " | ".join("" if pr.get(k) is None else f"{pr[k]:,}" for k in CURRENCIES) + " |")
            lines.append("")
    return "\n".join(lines)


# The skill has no tools: the same sentences, pointing at the reference file instead.
SKILL_WORDING = [
    ("are in the catalogue tool `brain_catalog`.", "are in references/catalog.md."),
    ("Always call `brain_catalog` for a price.", "Always take a price from references/catalog.md."),
    ("Call `brain_catalog` with the partner and country.", "Find the partner in references/catalog.md and use the country's column."),
    ("Call `brain_catalog` with a `category` to get a side-by-side", "Use the category section in references/catalog.md for a side-by-side"),
    ("(`brain_catalog` with a category shows the side-by-side)", "(the category section in references/catalog.md shows the side-by-side)"),
    ("(`brain_catalog` shows it)", "(see references/catalog.md)"),
    ("Always use `brain_catalog`: Salesforce wins.", "Always use references/catalog.md: Salesforce wins."),
    ("the bot pulls in Kareem or Hatem.", "ask Kareem Ibrahim or Hatem Ashour."),
    # 14-competitive-analysis
    ("Call `brain_catalog` with the category for the asker's country.", "Use the category section in references/catalog.md for the asker's country."),
    ("open the attached file with `read_slack_file`", "read the attached file"),
    ("**Find our match** with `brain_catalog`:", "**Find our match** in references/catalog.md:"),
    ("Our prices are list prices from `brain_catalog` only.", "Our prices are list prices from references/catalog.md only."),
    ("say so and call `escalate` with kind decision.", "say so, and name Kareem Ibrahim (Hatem Ashour when Kareem is away) for the decision."),
    ("(unified pricing), and call `escalate` with kind decision.", "(unified pricing), and name Kareem Ibrahim (Hatem Ashour when Kareem is away)."),
]


def knowledge_markdown() -> str:
    """The base knowledge files, minus the bot-only tool instructions (the skill has no tools)."""
    parts = ["# Reseller Program: rules and flows for every Foodics colleague", ""]
    for d in brain.load_docs(private=False):
        if d.audience != "base":
            continue
        body = re.sub(r"\n## When part of the question is locked at this level\n.*?(?=\n## |\Z)", "\n", d.body, flags=re.S)
        for tool_text, skill_text in SKILL_WORDING:
            body = body.replace(tool_text, skill_text)
        if "`brain_catalog`" in body or "`escalate`" in body:
            raise ValueError(f"{d.id}: tool wording left for the skill; add it to SKILL_WORDING")
        parts += [body.strip(), ""]
    return "\n".join(parts)


def build(skill_dir: Path = SKILL_DIR, zip_dir: Path | None = None) -> Path:
    catalog, knowledge = catalog_markdown(tools.Catalog()), knowledge_markdown()  # build both before writing either
    ref = skill_dir / "references" / "catalog.md"
    ref.parent.mkdir(parents=True, exist_ok=True)
    ref.write_text(catalog, encoding="utf-8")
    (skill_dir / "references" / "knowledge.md").write_text(knowledge, encoding="utf-8")
    if zip_dir:
        out = Path(zip_dir) / f"{skill_dir.name}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(skill_dir.rglob("*")):
                if p.is_file():
                    z.write(p, p.relative_to(skill_dir.parent))
        return out
    return ref


if __name__ == "__main__":
    zip_dir = sys.argv[sys.argv.index("--zip") + 1] if "--zip" in sys.argv else None
    print(build(zip_dir=Path(zip_dir) if zip_dir else None))

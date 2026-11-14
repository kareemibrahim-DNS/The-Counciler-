"""Builds the sales-only Claude skill (for @Claude in Slack) from the same catalogue the bot uses.

    python build_sales_skill.py            # rewrites ../sales-skill/reselling-brain-sales/references/catalog.md
    python build_sales_skill.py --zip DIR  # also writes DIR/reselling-brain-sales.zip to upload in claude.ai

The skill gets exactly the bot's sales view (Catalog.lookup at level "sales"): available resellers,
list prices and quote structure. No discount rules, cost, contacts, forms, Slack channels or team notes.
Claude in Slack gives everyone the same knowledge, so nothing above the sales layer may go in it.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import tools

SKILL_DIR = Path(__file__).resolve().parent.parent / "sales-skill" / "reselling-brain-sales"
CURRENCIES = {"SAR": "KSA (SAR)", "AED": "UAE (AED)", "KWD": "Kuwait (KWD)", "JOD": "Jordan (JOD)",
              "EGP": "Egypt (EGP)", "USD": "International (USD)"}


def catalog_markdown(cat: tools.Catalog) -> str:
    lines = ["# Reseller catalogue: available resellers, list prices, quote structure", "",
             "Source: Salesforce Standard Price Book + \"USD 1 – International\", exported 5 Nov 2026. LIST (selling) prices only.",
             "A blank price means the line is not sold in that country. Never convert between currencies.", "", "## Categories"]
    cats = json.loads(cat.lookup(level="sales"))["categories"]
    lines += [f"- **{c['name']}**: {', '.join(c['partners'])}" for c in cats] + [""]
    for c in cats:
        for p in c["partners"]:
            if p not in cat.partners:
                continue
            d = json.loads(cat.lookup(partner=p, level="sales"))
            lines.append(f"## {d['partner']}" + (" — INACTIVE, do not quote" if d["inactive"] else ""))
            lines += [f"- Category: {d['category']}", f"- What it is: {d['overview']}",
                      f"- Licensing unit: {d['licensing_unit']}", f"- Countries: {d['countries']}"]
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


def build(skill_dir: Path = SKILL_DIR, zip_dir: Path | None = None) -> Path:
    ref = skill_dir / "references" / "catalog.md"
    ref.parent.mkdir(parents=True, exist_ok=True)
    ref.write_text(catalog_markdown(tools.Catalog()), encoding="utf-8")
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

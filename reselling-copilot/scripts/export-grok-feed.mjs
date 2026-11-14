#!/usr/bin/env node
// Regenerates ../reseller-programs/feed/*.csv (the Grok Agent SDK bot) from reselling-copilot/data.
// One source of truth: Salesforce LIST prices only. No cost, markup or margin is ever written.
// Only signed, active resellers are exported.
// Sales layer (Kareem, 14 Nov 2026): only available resellers, list prices and commercial structure.
// No discount rules, internal notes, forms or Slack channels.
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const data = (f) => JSON.parse(readFileSync(join(here, "..", "data", f), "utf8"));
const out = join(here, "..", "..", "reseller-programs", "feed");

const catalog = data("catalog.json");
const partners = data("partners.json");
const categories = data("categories.json");

const CUR_COUNTRY = { SAR: "SA", AED: "AE", KWD: "KW", JOD: "JO", EGP: "EG" };
const SOURCE = "Source: Salesforce Standard Price Book, list prices, refreshed 14 Nov 2026.";

const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const csvCell = (v) => {
  const s = String(v ?? "");
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};
const toCsv = (header, rows) => [header.join(","), ...rows.map((r) => header.map((h) => csvCell(r[h])).join(","))].join("\n") + "\n";

const ASK = "Not available here. Please ask the Partnerships team.";
// Sales never sees discount rules or eligibility, not even "can't be discounted".
const noDiscount = (s) => !/discount/i.test(s);

const partnerRows = [];
const itemRows = [];
const priceRows = [];
const usedIds = new Set();

for (const cat of categories) {
  for (const name of cat.partners) {
    const m = partners[name];
    const items = catalog[name];
    if (!m || !items || m.inactive) continue;

    const countries = new Set();
    const billings = new Set();
    for (const l of items) {
      let id = `li-${slug(l.name)}`;
      while (usedIds.has(id)) id += "-x";
      usedIds.add(id);
      billings.add(l.f);
      itemRows.push({
        id,
        name: l.name,
        description: [`${name} · ${l.t}`, l.desc, l.flag ? `⚠ ${l.flag}` : ""].filter(Boolean).join(". "),
        unit: `${l.t} · ${l.f}`,
      });
      for (const [cur, cc] of Object.entries(CUR_COUNTRY)) {
        const amount = l.p[cur];
        if (amount == null) continue;
        countries.add(cc);
        priceRows.push({ line_item_id: id, country: cc, currency: cur, amount });
      }
    }
    if (!countries.size) continue;

    partnerRows.push({
      id: `partner-${slug(name)}`,
      name,
      countries: [...countries].join("|"),
      nature: `${cat.name}. ${m.overview}`,
      billing_model: `${m.unit} Quote rules: ${m.rules.filter(noDiscount).join(" ")}`,
      payment_terms: `Billing options in Salesforce: ${[...billings].join(", ")}.`,
      discount_policy: ASK,
      commercial_notes: `Prices are list (selling) prices per line per billing period. ${SOURCE}`,
      fulfillment: ASK,
      support_model: ASK,
      sla: ASK,
      operational_notes: `Working countries (partner guide): ${m.countries}. Quotable countries = countries with a Salesforce price.`,
    });
  }
}

// Product features such as a "Discount Card" in a line description are fine; Foodics discount rules are not.
const COMMERCIAL = ["billing_model", "payment_terms", "commercial_notes", "operational_notes"];
const leaks = partnerRows.flatMap((r) => COMMERCIAL.filter((k) => /discount/i.test(String(r[k]))).map((k) => `${r.id}.${k}`));
if (leaks.length) throw new Error(`Grok feed is sales-only and must not mention discounts: ${leaks.join(", ")}`);

writeFileSync(join(out, "partners.csv"), toCsv(
  ["id", "name", "countries", "nature", "billing_model", "payment_terms", "discount_policy", "commercial_notes", "fulfillment", "support_model", "sla", "operational_notes"],
  partnerRows,
));
writeFileSync(join(out, "line_items.csv"), toCsv(["id", "name", "description", "unit"], itemRows));
writeFileSync(join(out, "prices.csv"), toCsv(["line_item_id", "country", "currency", "amount"], priceRows));
console.log(`✔ Grok feed: ${partnerRows.length} partners, ${itemRows.length} line items, ${priceRows.length} prices.`);

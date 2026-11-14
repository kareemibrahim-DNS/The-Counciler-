#!/usr/bin/env node
// Refreshes LIST prices in data/catalog.json from Salesforce PricebookEntry query results.
// It never adds or removes lines (that is a product decision); it reports them instead.
//
// 1. Run this SOQL (Salesforce MCP or Workbench) and save each JSON result to a file:
//    SELECT Product2.Name, Product2.IsActive, Pricebook2.Name, CurrencyIsoCode, UnitPrice FROM PricebookEntry
//    WHERE IsActive = true AND (Pricebook2.IsStandard = true OR Pricebook2.Name LIKE 'USD 1%')
//    AND Product2.Family = 'Marketplace'
// 2. node scripts/refresh-prices.mjs <result.json> [more.json ...]
// 3. Copy data/catalog.json to reselling-brain/catalog/ and run the feed and skill builders (see README).
//
// Only UnitPrice (the selling price) is read. Cost, margin or markup fields are never requested or written.
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const file = join(dirname(fileURLToPath(import.meta.url)), "..", "data", "catalog.json");
const catalog = JSON.parse(readFileSync(file, "utf8"));
const CURRENCIES = ["SAR", "AED", "KWD", "JOD", "EGP", "USD"];
// Rough rates to SAR, only to spot prices that can't be right (a 2× gap or more between currencies; regional pricing stays below that).
const TO_SAR = { SAR: 1, AED: 1.02, KWD: 12.2, JOD: 5.29, USD: 3.75 };
const FLAG = "Prices are inconsistent across currencies in Salesforce. Verify before quoting.";
const DECIMALS = { KWD: 3, JOD: 3 }; // the rest use 2, as Salesforce shows them
const round = (v, c) => Number(Number(v).toFixed(DECIMALS[c] ?? 2));

const live = new Map();
const productActive = new Map();
for (const f of process.argv.slice(2)) {
  const { records } = JSON.parse(readFileSync(f, "utf8"));
  for (const r of records) {
    const name = r.Product2.Name;
    productActive.set(name, r.Product2.IsActive);
    if (!CURRENCIES.includes(r.CurrencyIsoCode)) continue;
    if (!live.has(name)) live.set(name, {});
    live.get(name)[r.CurrencyIsoCode] = round(r.UnitPrice, r.CurrencyIsoCode);
  }
}
if (!live.size) throw new Error("No PricebookEntry records given. Pass the saved SOQL JSON files.");

const report = { changed: [], notInSalesforce: [], newInSalesforce: [], flagged: [], unflagged: [] };
const known = new Set();
for (const [partner, items] of Object.entries(catalog)) {
  for (const l of items) {
    known.add(l.name);
    const p = live.get(l.name);
    if (!p || productActive.get(l.name) === false) { report.notInSalesforce.push(`${partner}: ${l.name}`); continue; }
    for (const c of CURRENCIES) {
      if ((l.p[c] ?? null) !== (p[c] ?? null)) report.changed.push(`${l.name} ${c}: ${l.p[c] ?? "—"} → ${p[c] ?? "—"}`);
    }
    // Keep the existing key order so the diff shows only real price changes.
    const order = [...Object.keys(l.p), ...CURRENCIES.filter((c) => !(c in l.p))];
    l.p = Object.fromEntries(order.filter((c) => p[c] != null).map((c) => [c, p[c]]));
    const sar = Object.entries(l.p).filter(([c]) => TO_SAR[c]).map(([c, v]) => v * TO_SAR[c]).filter((v) => v > 0);
    const bad = sar.length > 1 && Math.max(...sar) / Math.min(...sar) >= 2;
    if (bad && !l.flag) { l.flag = FLAG; report.flagged.push(l.name); }
    // A flag is only ever added here. Kareem removes it once the price book is fixed and checked.
    if (!bad && l.flag === FLAG) report.unflagged.push(`${l.name} (looks consistent now; flag kept until checked)`);
  }
}
for (const [name] of live) if (!known.has(name) && productActive.get(name)) report.newInSalesforce.push(name);

const original = readFileSync(file, "utf8");
writeFileSync(file, JSON.stringify(catalog, null, 1) + (original.endsWith("\n") ? "\n" : ""));
for (const [k, v] of Object.entries(report)) {
  console.log(`\n${k} (${v.length})`);
  for (const x of v) console.log(`  ${x}`);
}

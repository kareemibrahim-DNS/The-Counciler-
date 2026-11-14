#!/usr/bin/env node
// Fails the build if cost, margin or wholesale data ever lands in the repo's data or web page.
// This repo holds SELLING data only. Cost prices live in Partnerships' private sheets, never here.
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

const FORBIDDEN_KEY = /^(cost|costs|cost_price|costprice|buy|buy_price|wholesale|margin|markup|payout|commission)$/i;
const FORBIDDEN_TEXT = [/Cost \((SAR|AED|KWD|JOD|EGP|USD)\)/i, /Margin %/i, /Margin \(/i, /wholesale rate/i, /below (the )?(partner'?s )?list price/i];

const problems = [];

function walkKeys(node, path) {
  if (Array.isArray(node)) return node.forEach((v, i) => walkKeys(v, `${path}[${i}]`));
  if (node && typeof node === "object") {
    for (const [k, v] of Object.entries(node)) {
      if (FORBIDDEN_KEY.test(k)) problems.push(`${path}.${k}: forbidden field name`);
      walkKeys(v, `${path}.${k}`);
    }
  }
}

for (const f of readdirSync("data").filter((f) => f.endsWith(".json"))) {
  const file = join("data", f);
  walkKeys(JSON.parse(readFileSync(file, "utf8")), file);
}

for (const file of ["web/index.html", ...readdirSync("data").map((f) => join("data", f))]) {
  const text = readFileSync(file, "utf8");
  for (const re of FORBIDDEN_TEXT) if (re.test(text)) problems.push(`${file}: matches ${re}`);
}

// The Grok bot's feed (generated from data/ by export-grok-feed.mjs) must stay clean too.
const GROK_FEED = "../reseller-programs/feed";
let feedFiles = [];
try { feedFiles = readdirSync(GROK_FEED).filter((f) => f.endsWith(".csv")); } catch {}
for (const f of feedFiles) {
  const file = join(GROK_FEED, f);
  const text = readFileSync(file, "utf8");
  const header = text.split("\n")[0].split(",");
  for (const h of header) if (FORBIDDEN_KEY.test(h.trim())) problems.push(`${file}: forbidden column ${h}`);
  for (const re of [...FORBIDDEN_TEXT, /markup/i, /\bmargin\b/i, /wholesale/i]) if (re.test(text)) problems.push(`${file}: matches ${re}`);
}

// Reselling Brain (../reselling-brain): owner-only knowledge never lives in this shared repo.
// It reaches the bot through the BRAIN_OWNER_KNOWLEDGE_B64 secret instead.
const BRAIN = "../reselling-brain";
let brainFiles = [];
try { brainFiles = readdirSync(join(BRAIN, "knowledge")).filter((f) => f.endsWith(".md")); } catch {}
for (const f of brainFiles) {
  const file = join(BRAIN, "knowledge", f);
  const text = readFileSync(file, "utf8");
  const audience = (text.match(/^audience:\s*(\S+)/m) || [])[1];
  if (!["team", "sales"].includes(audience)) problems.push(`${file}: audience must be team or sales here (owner files stay out of this repo)`);
  if (/\b(30|27|23|20)\s?%/.test(text) && /markup/i.test(text) && /\|\s*(Monthly|Annual|Quarterly)[^|]*\|\s*\d+\s?%/i.test(text)) problems.push(`${file}: looks like a markup table`);
  if (/TARGET-NUMBER|TARGET-KPI/i.test(text)) problems.push(`${file}: looks like owner targets`);
}
try {
  for (const f of readdirSync(join(BRAIN, "catalog")).filter((x) => x.endsWith(".json"))) {
    walkKeys(JSON.parse(readFileSync(join(BRAIN, "catalog", f), "utf8")), join(BRAIN, "catalog", f));
  }
} catch {}

if (problems.length) {
  console.error("✖ Cost/margin data found. This repo must hold selling data only:\n  " + problems.join("\n  "));
  process.exit(1);
}
console.log(`✔ No cost, margin or wholesale data in data/, web/${feedFiles.length ? ", the Grok feed" : ""}${brainFiles.length ? " or the Reselling Brain" : ""}.`);

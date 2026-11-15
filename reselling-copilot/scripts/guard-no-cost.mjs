#!/usr/bin/env node
// Fails the build if cost, margin or wholesale data ever lands in the repo's data or web page.
// This repo holds SELLING data only. Cost prices live in Partnerships' private sheets, never here.
import { existsSync, readFileSync, readdirSync } from "node:fs";
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

// Team-only material (discount policy, partner channels, discount watch-outs) never lives in this
// shared repo either. It reaches the bots through secrets: BRAIN_OWNER_KNOWLEDGE_B64 and POLICY_JSON.
const PARTNER_CHANNEL = /#(ksa|uae|egypt|kw-jo|foodics)-[a-z]/i;
const DISCOUNT_BANDS = [/\d+\s?%\s?[–-]\s?\d+\s?%/, /of the (range|maximum)/i, /auto-rejected/i, /\bconst POLICY\b/];
for (const file of ["data/policy.json", "data/channels.json", "../reselling-brain/catalog/policy.json"]) {
  if (existsSync(file)) problems.push(`${file}: team-only discount policy or channel map (keep it in the secret)`);
}
for (const file of ["data/partners.json", "../reselling-brain/catalog/partners.json"]) {
  if (!existsSync(file)) continue;
  for (const [name, m] of Object.entries(JSON.parse(readFileSync(file, "utf8")))) {
    if ("slack" in m) problems.push(`${file}: ${name}.slack (partner channels are team-only)`);
    for (const k of ["watch", "rules", "edge", "unit"]) {
      if (/discount/i.test(JSON.stringify(m[k] ?? ""))) problems.push(`${file}: ${name}.${k} mentions discounts (team-only)`);
    }
  }
}
for (const file of ["web/index.html", ...readdirSync("data").map((f) => join("data", f))]) {
  const text = readFileSync(file, "utf8");
  if (PARTNER_CHANNEL.test(text)) problems.push(`${file}: names a partner channel (team-only)`);
  for (const re of DISCOUNT_BANDS) if (re.test(text)) problems.push(`${file}: looks like discount bands (${re})`);
}

// Real partner channel names (<country>-<partner>, foodics-<partner>) are team-only, in tests and comments too.
{
  const partners = JSON.parse(readFileSync("data/partners.json", "utf8"));
  const slugs = Object.keys(partners).filter((n) => !/[()]/.test(n)).map((n) => n.toLowerCase().replace(/[^a-z0-9]/g, ""));
  const REAL_CHANNEL = new RegExp(`\\b(ksa|uae|egypt|kw-jo|kw|jo|eg|foodics)-(${slugs.join("|")})\\b`, "i");
  const EXT = /\.(md|mdc|py|ts|js|mjs|ya?ml|json|html|csv|txt)$/;
  const walk = (dir) => {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      if (["node_modules", ".git", "dist", ".wrangler"].includes(e.name)) continue;
      const f = join(dir, e.name);
      if (e.isDirectory()) walk(f);
      else if (EXT.test(e.name)) {
        const m = readFileSync(f, "utf8").match(REAL_CHANNEL);
        if (m) problems.push(`${f}: names the partner channel "${m[0]}" (team-only; use a placeholder like ksa-partnera)`);
      }
    }
  };
  walk("..");
}

// Reselling Brain (../reselling-brain): only the common layer (base, sales) lives in this shared repo.
// Team, manager, cost and owner knowledge reaches the bot through the BRAIN_OWNER_KNOWLEDGE_B64 secret.
const BRAIN = "../reselling-brain";
let brainFiles = [];
try { brainFiles = readdirSync(join(BRAIN, "knowledge")).filter((f) => f.endsWith(".md")); } catch {}
for (const f of brainFiles) {
  const file = join(BRAIN, "knowledge", f);
  const text = readFileSync(file, "utf8");
  const audience = (text.match(/^audience:\s*(\S+)/m) || [])[1];
  if (!["base", "sales"].includes(audience)) problems.push(`${file}: audience must be base or sales here (team, manager, cost and owner files stay in the secret)`);
  if (PARTNER_CHANNEL.test(text)) problems.push(`${file}: names a partner channel (team-only)`);
  for (const re of DISCOUNT_BANDS) if (re.test(text)) problems.push(`${file}: looks like discount bands (${re})`);
  if (/markup/i.test(text) && /\|\s*(Monthly|Annual|Quarterly)[^|]*\|\s*\d+\s?%/i.test(text)) problems.push(`${file}: looks like a markup table`);
  // Targets or KPIs with real amounts are manager-only (no real values are written here).
  if (/\btargets?\b[^\n]{0,60}\d{1,3}(,\d{3}){2}|\$\d+(\.\d+)?M\b[^\n]{0,20}\bKPI\b/i.test(text)) problems.push(`${file}: looks like owner targets`);
  if (/\btracker\b/i.test(text)) problems.push(`${file}: names an internal tracker (trackers are for Kareem and Hatem only)`);
}
try {
  for (const f of readdirSync(join(BRAIN, "catalog")).filter((x) => x.endsWith(".json"))) {
    walkKeys(JSON.parse(readFileSync(join(BRAIN, "catalog", f), "utf8")), join(BRAIN, "catalog", f));
  }
} catch {}

if (problems.length) {
  console.error("✖ Cost, margin or team-only data found. This repo must hold the common layer only:\n  " + problems.join("\n  "));
  process.exit(1);
}
console.log(`✔ No cost, margin or wholesale data in data/, web/${feedFiles.length ? ", the Grok feed" : ""}${brainFiles.length ? " or the Reselling Brain" : ""}.`);

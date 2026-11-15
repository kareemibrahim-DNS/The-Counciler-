#!/usr/bin/env node
// Fails the build if cost, margin or wholesale data ever lands in the repo's data or web page.
// This repo holds SELLING data only. Cost prices live in Partnerships' private sheets, never here.
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { execFileSync } from "node:child_process";

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
// Any percentage range, or a percentage next to the word discount, looks like a discount band.
const DISCOUNT_BANDS = [/\d+\s?%\s?[–-]\s?\d+\s?%/, /discount[^\n]{0,60}\d+(\.\d+)?\s?%/i, /\d+(\.\d+)?\s?%[^\n]{0,40}discount/i, /\bconst POLICY\b/];
// A markup (هامش) and a percentage on the same line, or a markdown table with % cells in a file that mentions markup.
const MARKUP_WORD = /mark[- ]?up|هامش/i;
function looksLikeMarkup(text, isMarkdown) {
  const lines = text.split("\n");
  if (lines.some((l) => MARKUP_WORD.test(l) && /\d+(\.\d+)?\s?%/.test(l))) return true;
  return isMarkdown && MARKUP_WORD.test(text) && lines.some((l) => /^\s*\|.*\d+(\.\d+)?\s?%.*\|/.test(l));
}
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
const SKILL_REFS = "../reselling-brain/sales-skill/reselling-brain-sales";
const skillFiles = [];
try {
  skillFiles.push(join(SKILL_REFS, "SKILL.md"), ...readdirSync(join(SKILL_REFS, "references")).map((f) => join(SKILL_REFS, "references", f)));
} catch {}
for (const file of ["web/index.html", ...readdirSync("data").map((f) => join("data", f)), ...skillFiles.filter((f) => existsSync(f))]) {
  const text = readFileSync(file, "utf8");
  if (PARTNER_CHANNEL.test(text)) problems.push(`${file}: names a partner channel (team-only)`);
  for (const re of DISCOUNT_BANDS) if (re.test(text)) problems.push(`${file}: looks like discount bands (${re})`);
  if (looksLikeMarkup(text, file.endsWith(".md"))) problems.push(`${file}: looks like markup data`);
}

// Real partner channel names (<country>-<partner>, foodics-<partner>) are team-only, in tests and comments too.
// Every tracked text file is checked. Slack channel names are lowercase, so "Foodics-Xero integration" is fine.
{
  const partners = JSON.parse(readFileSync("data/partners.json", "utf8"));
  const words = (n) => n.replace(/\(.*?\)/g, " ").replace(/([a-z])([A-Z])/g, "$1 $2").toLowerCase().split(/[^a-z0-9]+/).filter(Boolean);
  const parts = [...new Set([...Object.keys(partners).map((n) => words(n).join("[-_]?")), "grub", "urban", "dynamics", "alpha"])];
  const REAL_CHANNEL = new RegExp(`(?<![\\w./-])(ksa|uae|egypt|kw-jo|kw|jo|eg|foodics)[-_](${parts.join("|")})(?![a-z0-9])`);
  let tracked = [];
  try {
    tracked = execFileSync("git", ["ls-files", "-z"], { cwd: "..", encoding: "utf8" }).split("\0").filter(Boolean);
  } catch {
    problems.push("git ls-files failed: run the guard inside the git checkout");
  }
  for (const rel of tracked) {
    if (/\.(bundle|png|jpe?g|gif|ico|pdf|zip|woff2?)$/i.test(rel) || /(^|\/)package-lock\.json$/.test(rel)) continue;
    let text;
    try { text = readFileSync(join("..", rel), "utf8"); } catch { continue; }
    if (text.includes("\0")) continue;
    const m = text.match(REAL_CHANNEL);
    if (m) problems.push(`${rel}: names the partner channel "${m[0]}" (team-only; use a placeholder like ksa-partnera)`);
  }
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
  if (looksLikeMarkup(text, true)) problems.push(`${file}: looks like markup data`);
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

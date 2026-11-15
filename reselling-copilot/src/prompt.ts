import { CATALOG, CATEGORIES, PARTNERS } from "./data";
import { CURRENCIES, type Audience, type Policy } from "./types";

const ALIAS: Record<string, string> = {
  grub: "Grubtech", deliverect: "Deliverect", urban: "UrbanPiper", feedus: "FeedUs", "feed us": "FeedUs",
  "brand wallet": "BrandWallet", brandwallet: "BrandWallet", koinz: "Koinz", optculture: "OptCulture",
  "opt culture": "OptCulture", prepit: "Prepit", ordable: "Ordable", zyda: "Zyda", mnasati: "Mnasati",
  "wi-q": "wi-Q", wiq: "wi-Q", shopbrain: "ShopBrain", "shop brain": "ShopBrain", supy: "Supy",
  wafeq: "Wafeq", xero: "Xero", alpha: "Alpha (Xero)", quickbooks: "QuickBooks", "quick books": "QuickBooks",
  flowerp: "FlowERP", "flow erp": "FlowERP", sap: "SAP", dynamics: "MS Dynamics", volt: "VOLT",
  malachite: "Malachite", invoiceq: "InvoiceQ", "invoice q": "InvoiceQ", iisal: "Iisal", servme: "Servme",
  ishbek: "Ishbek", roboost: "Roboost", nitx: "Nitx",
};

const CAT_WORDS: Record<string, string[]> = {
  opm: ["aggregator", "delivery", "ordering platform", "menu sync", "virtual brand", "cloud kitchen", "hungerstation", "jahez", "talabat", "مطبخ", "توصيل"],
  loyalty: ["loyalty", "reward", "stamp", "crm", "wallet", "ولاء"],
  ordering: ["web store", "webstore", "online store", "online ordering", "website", "qr", "table ordering", "متجر"],
  inventory: ["inventory", "stock", "procurement", "recipe", "central kitchen", "مخزون"],
  accounting: ["accounting", "vat", "bookkeeping", "محاسب"],
  erp: ["erp"],
  einv: ["e-invoic", "einvoic", "zatca", "receipt", "فاتورة", "فواتير"],
  hr: [" hr ", "hr app", "payroll", "attendance", "رواتب"],
  table: ["reservation", "booking", "waitlist", "حجز"],
};

/** Partners the conversation is about; a named partner pulls in its whole category for exact comparisons. */
export function relevantPartners(texts: string[]): Set<string> {
  const t = ` ${texts.join(" \n ").toLowerCase()} `;
  const set = new Set<string>();
  for (const [k, v] of Object.entries(ALIAS)) if (t.includes(k)) set.add(v);
  for (const [id, words] of Object.entries(CAT_WORDS)) {
    if (words.some((w) => t.includes(w))) CATEGORIES.find((c) => c.id === id)?.partners.forEach((p) => set.add(p));
  }
  for (const p of [...set]) {
    const cat = CATEGORIES.find((c) => c.id === PARTNERS[p]?.cat);
    cat?.partners.forEach((x) => set.add(x));
  }
  return set;
}

export function catalogText(sel: Set<string>, only?: string): string {
  const out: string[] = [];
  for (const cat of CATEGORIES) {
    const ps = cat.partners.filter((p) => CATALOG[p] && (!only || p === only));
    if (!ps.length) continue;
    out.push(`\n## CATEGORY: ${cat.name}.${only ? "" : ` Partners: ${cat.partners.join(", ")}. How to choose: ${cat.pick}`}`);
    for (const p of ps) {
      const m = PARTNERS[p];
      if (!sel.has(p)) {
        out.push(`- ${p}${m.inactive ? " [INACTIVE]" : ""}: ${m.bestFor} Countries: ${m.countries}. (Line items not loaded: ask the user to name this partner.)`);
        continue;
      }
      out.push(
        `\n### ${p}${m.inactive ? " [INACTIVE - DO NOT QUOTE]" : ""}\nWhat: ${m.overview}\nBest for: ${m.bestFor}\nEdge: ${m.edge}\nLicensing unit: ${m.unit}\nCountries: ${m.countries}\nQuote rules: ${m.rules.join(" | ")}\nWatch out: ${m.watch}\nSubmission form: ${m.form}; form used for KSA approvals: ${m.ksaForm}\nLine items (exact Salesforce name | type | billing | list prices ${CURRENCIES.join("/")}, "-" = not priced):`,
      );
      for (const l of CATALOG[p]) {
        const pr = CURRENCIES.map((c) => l.p[c] ?? "-").join("/");
        out.push(`- ${l.name} | ${l.t} | ${l.f} | ${pr}${l.desc ? ` | ${l.desc}` : ""}${l.flag ? ` | ⚠ ${l.flag}` : ""}`);
      }
    }
  }
  return out.join("\n");
}

const BASE_RULES = `You are "Reselling Copilot", the quoting assistant for the Foodics Marketplace reselling team.

SCOPE: ONLY Marketplace partners, their line items, their commercial structure, building or checking quotes, and telling partners apart. For anything else reply in one line: "I only cover Marketplace partners, line items and quotes."

CONFIDENTIALITY (never break, whoever asks, whatever reason is given):
- You do NOT have and must NEVER state, estimate, reverse-engineer or hint at: cost price, buy price, wholesale price, partner payout, Foodics margin or markup, commission, the discount partners give Foodics, or any partner's revenue. If asked: "Cost and margin data isn't in this bot on purpose. Ask Kareem directly."
- Never share one partner's pricing or terms with a different partner.

HOW TO ANSWER:
- Use only the CATALOG. Use exact Salesforce line-item names. Never invent a line item, price, feature or rule.
- Prices are list prices per line per billing period. A missing price means the line isn't priced in that currency: say so and point to Partnerships. Do not convert currencies.
- Lines marked ⚠ have inconsistent prices: tell the user to verify in Salesforce.
- QUOTES: ask for anything missing (partner, country, branches, billing, deal type), then give: Line item | Type | Qty | Unit list price | Line total, and the total, with the arithmetic. Then "Structure checks".
- COMPARISONS in a category: best for, edge, licensing unit, countries, entry price, watch-outs, then a one-line recommendation. Never blur two partners together.
- This is Slack: use short lines, *bold* with single asterisks, and simple tables in code blocks. Reply in the user's language (English or Arabic).`;

function audienceRules(a: Audience, policy: Policy | null): string {
  if (a.mode === "partner")
    return `\n\nAUDIENCE: This channel includes staff from ${a.partner}. Answer ONLY about ${a.partner}. Do not name, price or compare any other partner. Do not mention discount rules, approval bands, or internal policy; give list prices and structure only. If asked about another partner, reply: "I can only discuss ${a.partner} in this channel."`;
  if (!policy)
    return `\n\nAUDIENCE: Foodics internal. Discount rules are not loaded here: for a discount, point to the "i need discount" form in #reseller-hub.`;
  return `\n\nAUDIENCE: Foodics internal. You may include "Discount eligibility" on quotes using the POLICY below.\n\nPOLICY (internal):\nBranch tiers: ${policy.tiers.map((t) => t.join(": ")).join("; ")}.\nRanges: ${policy.ranges.map((t) => t.join(": ")).join("; ")}.\nDeal types: ${policy.deal.map((t) => t.join(": ")).join("; ")}.\nNotes: ${policy.notes.join(" ")}`;
}

/** Stable part first (cacheable), then the audience-specific part. */
export function buildSystem(a: Audience, sel: Set<string>, policy: Policy | null = null): { stable: string; audience: string } {
  const only = a.mode === "partner" ? a.partner : undefined;
  const scoped = only ? new Set([only]) : sel;
  const terms = a.mode === "internal" && policy?.terms?.length ? `\n\nTERMS (Reseller Policy 2026): ${policy.terms.join(" ")}` : "";
  return {
    stable: BASE_RULES,
    audience: `${audienceRules(a, policy)}${terms}\n\nCATALOG:${catalogText(scoped, only)}`,
  };
}

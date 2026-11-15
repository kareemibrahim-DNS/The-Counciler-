export type Currency = "SAR" | "AED" | "KWD" | "JOD" | "EGP" | "USD";
export const CURRENCIES: Currency[] = ["SAR", "AED", "KWD", "JOD", "EGP", "USD"];

export interface LineItem {
  name: string; // exact Salesforce product name
  code: string;
  desc: string;
  p: Partial<Record<Currency, number>>; // LIST (selling) prices only
  f: string; // billing frequency
  t: "Main" | "Additional" | "Add-on" | "One-time" | "Usage";
  flag?: string;
}

export interface Partner {
  cat: string;
  countries: string;
  slack?: string; // team-only; not kept in this repo
  form: string;
  ksaForm: string;
  overview: string;
  bestFor: string;
  unit: string;
  edge: string;
  watch: string;
  rules: string[];
  inactive?: boolean;
}

export interface Category {
  id: string;
  name: string;
  partners: string[];
  pick: string;
}

export interface Policy {
  tiers: [string, string][];
  ranges: [string, string][];
  deal: [string, string][];
  notes: string[];
  terms: string[];
}

/** Where the bot is talking decides what it may say. */
export type Audience =
  | { mode: "internal" } // Foodics-only channel or DM
  | { mode: "partner"; partner: string } // shared channel with one partner's staff
  | { mode: "external" }; // shared/external channel we can't map to a partner

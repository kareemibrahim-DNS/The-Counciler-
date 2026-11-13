import catalog from "../data/catalog.json";
import partners from "../data/partners.json";
import categories from "../data/categories.json";
import policy from "../data/policy.json";
import channels from "../data/channels.json";
import type { Category, LineItem, Partner, Policy } from "./types";

export const CATALOG = catalog as unknown as Record<string, LineItem[]>;
export const PARTNERS = partners as unknown as Record<string, Partner>;
export const CATEGORIES = categories as unknown as Category[];
export const POLICY = policy as unknown as Policy;
export const CHANNEL_PARTNER = Object.fromEntries(
  Object.entries(channels).filter(([k]) => !k.startsWith("_")),
) as Record<string, string>;

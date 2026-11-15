import catalog from "../data/catalog.json";
import partners from "../data/partners.json";
import categories from "../data/categories.json";
import type { Category, LineItem, Partner, Policy } from "./types";

export const CATALOG = catalog as unknown as Record<string, LineItem[]>;
export const PARTNERS = partners as unknown as Record<string, Partner>;
export const CATEGORIES = categories as unknown as Category[];

/**
 * The discount policy and the partner-channel map are team-only, so they are not in this repo.
 * The worker reads them from the POLICY_JSON secret ({"policy": {"text", "terms"}, "channels": {name: partner}}).
 * Without it, internal answers carry no discount rules and every partner-named channel is refused.
 */
export function teamData(raw?: string): { policy: Policy | null; channels: Record<string, string> } {
  if (!raw) return { policy: null, channels: {} };
  try {
    const d = JSON.parse(raw) as { policy?: Policy; channels?: Record<string, string> };
    const channels = Object.fromEntries(Object.entries(d.channels || {}).filter(([k]) => !k.startsWith("_")));
    const policy = d.policy && typeof d.policy.text === "string" && d.policy.text.trim() ? d.policy : null;
    return { policy, channels };
  } catch {
    return { policy: null, channels: {} };
  }
}

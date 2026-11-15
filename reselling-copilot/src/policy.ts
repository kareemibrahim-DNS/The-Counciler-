import type { Audience } from "./types";

export interface ChannelInfo {
  name?: string;
  isIm: boolean;
  isExtShared: boolean;
}

/** Partner channels follow these names (#ksa-…, #uae-…, #egypt-…, #kw-jo-…, #foodics-…). */
export const PARTNER_CHANNEL = /^(ksa|uae|egypt|kw-jo|foodics)-/i;

/**
 * Decide who can read the reply.
 * - Channels mapped in the POLICY_JSON secret include partner staff → partner mode.
 * - Any other shared channel, or one named like a partner channel → external mode (no pricing at all).
 * - DMs and internal channels → internal mode.
 * A partner-named channel is never internal, even if Slack doesn't mark it as shared,
 * because partner members are invited directly into these channels.
 */
export function audienceFor(ch: ChannelInfo, channels: Record<string, string> = {}): Audience {
  const partner = ch.name ? channels[ch.name] : undefined;
  if (partner) return { mode: "partner", partner };
  if (ch.isExtShared || (ch.name && PARTNER_CHANNEL.test(ch.name))) return { mode: "external" };
  return { mode: "internal" };
}

const COST_WORDS =
  /\b(cost|wholesale|margin|markup|mark-up|buy price|purchase price|payout|commission|profit)\b|تكلفة|هامش|سعر الشراء|الجملة|ربح/i;

/** True when the question asks for data this bot must never give. */
export function asksForCost(text: string): boolean {
  return COST_WORDS.test(text) && !/list price|سعر البيع/i.test(text);
}

export const COST_REFUSAL =
  "Cost and margin data isn't in this bot on purpose. Ask Kareem directly. I can give you list prices and line-item structure.";

export const EXTERNAL_REFUSAL =
  "I can't share commercial details in this channel. Please contact the Foodics Partnerships team.";

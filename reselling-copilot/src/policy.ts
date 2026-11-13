import { CHANNEL_PARTNER } from "./data";
import type { Audience } from "./types";

export interface ChannelInfo {
  name?: string;
  isIm: boolean;
  isExtShared: boolean;
}

/**
 * Decide who can read the reply.
 * - Mapped partner channels (e.g. #ksa-grubtech) include partner staff → partner mode.
 * - Any other externally shared channel → external mode (no pricing at all).
 * - DMs and internal channels → internal mode.
 * A mapped channel is always partner mode, even if Slack doesn't mark it as shared,
 * because partner members are invited directly into these channels.
 */
export function audienceFor(ch: ChannelInfo): Audience {
  const partner = ch.name ? CHANNEL_PARTNER[ch.name] : undefined;
  if (partner) return { mode: "partner", partner };
  if (ch.isExtShared) return { mode: "external" };
  return { mode: "internal" };
}

const COST_WORDS =
  /\b(cost|wholesale|margin|markup|mark-up|buy price|purchase price|payout|commission|profit)\b|تكلفة|هامش|سعر الشراء|الجملة|ربح/i;

/** True when the question asks for data this bot must never give. */
export function asksForCost(text: string): boolean {
  return COST_WORDS.test(text) && !/list price|سعر البيع/i.test(text);
}

export const COST_REFUSAL =
  "Cost and margin data isn't in this bot on purpose. Ask Kareem directly. I can give you list prices, line-item structure and discount eligibility.";

export const EXTERNAL_REFUSAL =
  "I can't share commercial details in this channel. Please contact the Foodics Partnerships team.";

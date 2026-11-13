import { prompt } from "@grok/agent-sdk";
import { defineTool } from "@grok/agent-sdk/tools";
import * as z from "zod/v4";
import { findQuoteStructure } from "../lib/catalog.js";

export default defineTool({
  description: prompt`
    Return the Commercial and Operational quote structure for one
    partner. Each partner has its own nature — never reuse another
    partner's commercial or operational terms. Prefer partnerId from
    list_partners; partnerName is a fallback. Optional country checks
    that the partner operates there.
  `,
  effect: "read",
  inputSchema: z.object({
    partnerId: z.string().optional().describe("Partner id from list_partners"),
    partnerName: z.string().optional().describe("Partner display name"),
    country: z
      .string()
      .optional()
      .describe("ISO country to verify partner coverage"),
  }),
  async execute(input) {
    if (!input.partnerId && !input.partnerName) {
      return {
        ok: false,
        error: "partnerId or partnerName is required.",
        note: "Call list_partners first, then request quote structure for one partner.",
      };
    }
    return findQuoteStructure(input);
  },
});

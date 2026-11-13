import { prompt } from "@grok/agent-sdk";
import { defineTool } from "@grok/agent-sdk/tools";
import * as z from "zod/v4";
import { findLineItemPrice } from "../lib/catalog.js";

export default defineTool({
  description: prompt`
    Look up the price of one line item for one country.
    Country is required — every country has its own price. Never answer
    with another country's amount. Prefer lineItemId from
    list_line_items; lineItemName is a fallback.
  `,
  effect: "read",
  inputSchema: z.object({
    lineItemId: z.string().optional().describe("Line item id"),
    lineItemName: z.string().optional().describe("Line item name"),
    country: z
      .string()
      .describe("ISO 3166-1 alpha-2 country code — required for price"),
  }),
  async execute(input) {
    if (!input.lineItemId && !input.lineItemName) {
      return {
        ok: false,
        error: "lineItemId or lineItemName is required.",
        note: "Call list_line_items first.",
      };
    }
    return findLineItemPrice(input);
  },
});

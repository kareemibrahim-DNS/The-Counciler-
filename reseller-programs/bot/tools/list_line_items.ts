import { prompt } from "@grok/agent-sdk";
import { defineTool } from "@grok/agent-sdk/tools";
import * as z from "zod/v4";
import { findLineItems } from "../lib/catalog.js";

export default defineTool({
  description: prompt`
    List available reseller line items (SKUs).
    Does not return prices — prices are country-specific; use
    get_line_item_price with a country.
  `,
  effect: "read",
  inputSchema: z.object({}),
  async execute() {
    return findLineItems();
  },
});

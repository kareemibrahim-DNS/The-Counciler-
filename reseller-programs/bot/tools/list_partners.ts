import { prompt } from "@grok/agent-sdk";
import { defineTool } from "@grok/agent-sdk/tools";
import * as z from "zod/v4";
import { findPartners } from "../lib/catalog.js";

export default defineTool({
  description: prompt`
    List reseller-program partners.
    Pass country (ISO alpha-2, e.g. SA, AE, EG) to filter — partner
    availability depends on country. Omit country only when the user
    wants the full catalog, then remind them to filter by country.
  `,
  effect: "read",
  inputSchema: z.object({
    country: z
      .string()
      .optional()
      .describe("ISO 3166-1 alpha-2 country code, e.g. SA"),
  }),
  async execute({ country }) {
    return findPartners(country);
  },
});

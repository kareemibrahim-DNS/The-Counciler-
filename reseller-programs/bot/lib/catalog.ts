/**
 * Reseller program catalog — query helpers.
 *
 * Authoritative rows live in feed/*.csv. Regenerate with:
 *   npm run feed
 * which writes bot/lib/catalog.data.ts
 */

import {
  lineItems as feedLineItems,
  partners as feedPartners,
  prices as feedPrices,
} from "./catalog.data.js";

export type CountryCode = string;

export type Partner = {
  id: string;
  name: string;
  /** ISO 3166-1 alpha-2 countries where this partner operates. */
  countries: CountryCode[];
  /** Short note on the partner's commercial/ops nature. */
  nature: string;
  commercial: {
    quoteType: "Commercial";
    billingModel: string;
    paymentTerms: string;
    discountPolicy: string;
    notes: string;
  };
  operational: {
    quoteType: "Operational";
    fulfillment: string;
    supportModel: string;
    sla: string;
    notes: string;
  };
};

export type LineItem = {
  id: string;
  name: string;
  description: string;
  unit: string;
};

export type CountryPrice = {
  lineItemId: string;
  country: CountryCode;
  currency: string;
  amount: number;
};

export type PublicPartner = {
  id: string;
  name: string;
  countries: CountryCode[];
  nature: string;
};

export const partners: Partner[] = feedPartners;
export const lineItems: LineItem[] = feedLineItems;
export const prices: CountryPrice[] = feedPrices;

export function normalizeCountry(raw: string): string {
  return raw.trim().toUpperCase();
}

export function findPartners(country?: string): {
  partners: PublicPartner[];
  countryFilter: string | null;
  note: string;
} {
  if (!country) {
    return {
      partners: partners.map(publicPartner),
      countryFilter: null,
      note: "All partners listed. Partner availability depends on country — ask for a country to filter.",
    };
  }
  const code = normalizeCountry(country);
  const matched = partners.filter((p) =>
    p.countries.map(normalizeCountry).includes(code),
  );
  return {
    partners: matched.map(publicPartner),
    countryFilter: code,
    note:
      matched.length > 0
        ? `Partners that operate in ${code}.`
        : `No partner in the catalog operates in ${code}.`,
  };
}

export function findLineItems(): { lineItems: LineItem[]; note: string } {
  return {
    lineItems: [...lineItems],
    note: "Available reseller line items. Prices are country-specific — call get_line_item_price with a country.",
  };
}

export function findQuoteStructure(input: {
  partnerId?: string;
  partnerName?: string;
  country?: string;
}): {
  ok: boolean;
  partner?: PublicPartner;
  commercial?: Partner["commercial"];
  operational?: Partner["operational"];
  error?: string;
  note: string;
} {
  const partner = resolvePartner(input.partnerId, input.partnerName);
  if (!partner) {
    return {
      ok: false,
      error: "Partner not found. Call list_partners first.",
      note: "Quote structure is partner-specific.",
    };
  }
  if (input.country) {
    const code = normalizeCountry(input.country);
    if (!partner.countries.map(normalizeCountry).includes(code)) {
      return {
        ok: false,
        partner: publicPartner(partner),
        error: `Partner ${partner.name} does not operate in ${code}.`,
        note: "Do not apply this partner's quote structure outside its countries.",
      };
    }
  }
  return {
    ok: true,
    partner: publicPartner(partner),
    commercial: partner.commercial,
    operational: partner.operational,
    note: "Commercial and Operational structures follow this partner's own nature. Do not mix with another partner.",
  };
}

export function findLineItemPrice(input: {
  lineItemId?: string;
  lineItemName?: string;
  country: string;
}): {
  ok: boolean;
  lineItem?: LineItem;
  country?: string;
  currency?: string;
  amount?: number;
  unit?: string;
  error?: string;
  availableCountries?: string[];
  note: string;
} {
  const code = normalizeCountry(input.country);
  if (!code) {
    return {
      ok: false,
      error: "country is required. Prices differ by country.",
      note: "Never answer a price without a country.",
    };
  }
  const item = resolveLineItem(input.lineItemId, input.lineItemName);
  if (!item) {
    return {
      ok: false,
      error: "Line item not found. Call list_line_items first.",
      note: "Unknown line item.",
    };
  }
  const row = prices.find(
    (p) =>
      p.lineItemId === item.id && normalizeCountry(p.country) === code,
  );
  const availableCountries = prices
    .filter((p) => p.lineItemId === item.id)
    .map((p) => p.country);
  if (!row) {
    return {
      ok: false,
      lineItem: item,
      country: code,
      error: `No price for ${item.name} in ${code}.`,
      availableCountries,
      note: "Do not reuse another country's price.",
    };
  }
  return {
    ok: true,
    lineItem: item,
    country: code,
    currency: row.currency,
    amount: row.amount,
    unit: item.unit,
    availableCountries,
    note: `Price is for ${code} only. Other countries have different amounts.`,
  };
}

function publicPartner(p: Partner): PublicPartner {
  return {
    id: p.id,
    name: p.name,
    countries: [...p.countries],
    nature: p.nature,
  };
}

function resolvePartner(
  id?: string,
  name?: string,
): Partner | undefined {
  if (id) {
    const byId = partners.find(
      (p) => p.id.toLowerCase() === id.trim().toLowerCase(),
    );
    if (byId) return byId;
  }
  if (name) {
    const needle = name.trim().toLowerCase();
    return partners.find(
      (p) =>
        p.name.toLowerCase() === needle ||
        p.name.toLowerCase().includes(needle) ||
        p.id.toLowerCase() === needle,
    );
  }
  return undefined;
}

function resolveLineItem(
  id?: string,
  name?: string,
): LineItem | undefined {
  if (id) {
    const byId = lineItems.find(
      (i) => i.id.toLowerCase() === id.trim().toLowerCase(),
    );
    if (byId) return byId;
  }
  if (name) {
    const needle = name.trim().toLowerCase();
    return lineItems.find(
      (i) =>
        i.name.toLowerCase() === needle ||
        i.name.toLowerCase().includes(needle) ||
        i.id.toLowerCase() === needle,
    );
  }
  return undefined;
}

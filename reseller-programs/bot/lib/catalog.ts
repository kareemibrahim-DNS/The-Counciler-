/**
 * Reseller program catalog.
 *
 * Replace SAMPLE_* rows with your real partner, line-item, and country
 * price data. Tools never invent prices or partners outside this file.
 */

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

/** SAMPLE data — update before production use. */
export const partners: Partner[] = [
  {
    id: "partner-dns-sa",
    name: "DNS Gulf Resellers",
    countries: ["SA", "BH", "KW"],
    nature:
      "Regional distributor with its own credit terms and local-stock fulfillment.",
    commercial: {
      quoteType: "Commercial",
      billingModel: "Partner-invoiced; monthly consolidated billing",
      paymentTerms: "Net 30 from invoice date",
      discountPolicy: "Tiered volume discount by quarterly commit",
      notes:
        "Commercial quotes must use this partner's billing model and payment terms — do not reuse another partner's commercial terms.",
    },
    operational: {
      quoteType: "Operational",
      fulfillment: "Local warehouse in Riyadh; cross-border for BH/KW",
      supportModel: "Partner L1, vendor L2/L3 via ticket",
      sla: "Next-business-day for in-stock SKUs in SA",
      notes:
        "Operational quotes follow this partner's fulfillment and SLA — they differ from UAE partners.",
    },
  },
  {
    id: "partner-me-cloud",
    name: "ME Cloud Partners",
    countries: ["AE", "OM", "QA"],
    nature:
      "Cloud-first reseller; quotes are subscription-led with usage true-up.",
    commercial: {
      quoteType: "Commercial",
      billingModel: "Subscription + usage true-up",
      paymentTerms: "Net 15 prepaid for first term",
      discountPolicy: "Fixed partner margin; no end-customer discount stack",
      notes:
        "Commercial structure is subscription-led. Do not quote one-time CAPEX terms for this partner.",
    },
    operational: {
      quoteType: "Operational",
      fulfillment: "Digital provisioning within 24h of PO",
      supportModel: "Partner-managed tenant; vendor portal for escalations",
      sla: "P1 4h response via partner queue",
      notes:
        "Operational structure assumes digital delivery — no physical stock.",
    },
  },
  {
    id: "partner-egypt-channel",
    name: "Nile Channel Co.",
    countries: ["EG"],
    nature:
      "Single-country channel partner; local currency and local VAT handling.",
    commercial: {
      quoteType: "Commercial",
      billingModel: "Local EGP invoice with VAT",
      paymentTerms: "Net 45",
      discountPolicy: "Deal-registration protected margin",
      notes:
        "Commercial quotes must be in EGP structure; do not quote USD list as customer price.",
    },
    operational: {
      quoteType: "Operational",
      fulfillment: "Cairo DC + partner last-mile",
      supportModel: "Arabic-first partner support desk",
      sla: "2 business days for standard SKUs",
      notes: "Operational coverage is Egypt-only.",
    },
  },
];

/** SAMPLE data — update before production use. */
export const lineItems: LineItem[] = [
  {
    id: "li-core-seat",
    name: "Core Seat",
    description: "Named-user seat for the core product.",
    unit: "seat / year",
  },
  {
    id: "li-storage-tb",
    name: "Storage Pack",
    description: "Additional storage capacity pack.",
    unit: "TB / year",
  },
  {
    id: "li-premium-support",
    name: "Premium Support",
    description: "Premium support uplift for covered seats.",
    unit: "seat / year",
  },
  {
    id: "li-onboarding",
    name: "Onboarding Package",
    description: "One-time partner-led onboarding engagement.",
    unit: "engagement",
  },
];

/** SAMPLE data — prices are per country; never reuse across countries. */
export const prices: CountryPrice[] = [
  { lineItemId: "li-core-seat", country: "SA", currency: "SAR", amount: 1200 },
  { lineItemId: "li-core-seat", country: "AE", currency: "AED", amount: 1100 },
  { lineItemId: "li-core-seat", country: "EG", currency: "EGP", amount: 9500 },
  { lineItemId: "li-core-seat", country: "BH", currency: "BHD", amount: 110 },
  { lineItemId: "li-core-seat", country: "KW", currency: "KWD", amount: 95 },
  { lineItemId: "li-core-seat", country: "OM", currency: "OMR", amount: 115 },
  { lineItemId: "li-core-seat", country: "QA", currency: "QAR", amount: 1050 },

  { lineItemId: "li-storage-tb", country: "SA", currency: "SAR", amount: 450 },
  { lineItemId: "li-storage-tb", country: "AE", currency: "AED", amount: 420 },
  { lineItemId: "li-storage-tb", country: "EG", currency: "EGP", amount: 3800 },

  {
    lineItemId: "li-premium-support",
    country: "SA",
    currency: "SAR",
    amount: 300,
  },
  {
    lineItemId: "li-premium-support",
    country: "AE",
    currency: "AED",
    amount: 280,
  },
  {
    lineItemId: "li-premium-support",
    country: "EG",
    currency: "EGP",
    amount: 2400,
  },

  {
    lineItemId: "li-onboarding",
    country: "SA",
    currency: "SAR",
    amount: 15000,
  },
  {
    lineItemId: "li-onboarding",
    country: "AE",
    currency: "AED",
    amount: 14000,
  },
  {
    lineItemId: "li-onboarding",
    country: "EG",
    currency: "EGP",
    amount: 125000,
  },
];

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

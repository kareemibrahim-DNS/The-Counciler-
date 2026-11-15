import { describe, expect, it } from "vitest";
import { CATALOG, CATEGORIES, PARTNERS, teamData } from "../src/data";
import { asksForCost, audienceFor } from "../src/policy";
import { buildSystem, relevantPartners } from "../src/prompt";
import type { Policy } from "../src/types";

const POLICY: Policy = { text: "POLICY-TEXT-MARKER", terms: ["TERMS-MARKER"] };

describe("audience", () => {
  it("treats channels mapped in the secret as partner-only", () => {
    const channels = { "partner-x": "Grubtech" };
    expect(audienceFor({ name: "partner-x", isIm: false, isExtShared: false }, channels)).toEqual({ mode: "partner", partner: "Grubtech" });
  });
  it("refuses partner-named channels even without the secret", () => {
    for (const name of ["ksa-w", "uae-v", "egypt-x", "kw-jo-y", "foodics-z"])
      expect(audienceFor({ name, isIm: false, isExtShared: false }).mode, name).toBe("external");
  });
  it("refuses unmapped shared channels", () => {
    expect(audienceFor({ name: "random-shared", isIm: false, isExtShared: true })).toEqual({ mode: "external" });
  });
  it("treats DMs and internal channels as internal", () => {
    expect(audienceFor({ isIm: true, isExtShared: false }).mode).toBe("internal");
    expect(audienceFor({ name: "reselling-team", isIm: false, isExtShared: false }).mode).toBe("internal");
  });
});

describe("cost questions", () => {
  it("blocks cost and margin questions in English and Arabic", () => {
    expect(asksForCost("what is the cost of Grubtech?")).toBe(true);
    expect(asksForCost("what margin do we make on Supy")).toBe(true);
    expect(asksForCost("كم التكلفة")).toBe(true);
  });
  it("allows normal quote questions", () => {
    expect(asksForCost("quote ShopBrain for 6 branches")).toBe(false);
    expect(asksForCost("ShopBrain cost center line item list price")).toBe(false);
  });
});

describe("prompt scoping", () => {
  it("loads the whole category when one partner is named", () => {
    const sel = relevantPartners(["grubtech for 4 branches"]);
    for (const p of ["Grubtech", "Deliverect", "UrbanPiper", "FeedUs"]) expect(sel.has(p)).toBe(true);
    expect(sel.has("Supy")).toBe(false);
  });
  it("in a partner channel, mentions no other partner's line items or the discount policy", () => {
    const { stable, audience } = buildSystem({ mode: "partner", partner: "Grubtech" }, new Set(["Grubtech", "Deliverect"]), POLICY);
    expect(audience).toContain("Grubtech - gOnline License");
    expect(audience).not.toContain("Deliverect - Physical License");
    expect(stable + audience).not.toContain("POLICY-TEXT-MARKER");
    expect(stable + audience).not.toContain("TERMS-MARKER");
  });
  it("internal prompt includes the discount policy only when the secret provides it", () => {
    expect(buildSystem({ mode: "internal" }, new Set(), POLICY).audience).toContain("POLICY (internal):\nPOLICY-TEXT-MARKER");
    expect(buildSystem({ mode: "internal" }, new Set(), POLICY).audience).toContain("TERMS-MARKER");
    const bare = buildSystem({ mode: "internal" }, new Set());
    expect(bare.stable + bare.audience).not.toContain("POLICY (internal)");
    expect(bare.audience).toContain("i need discount");
  });
  it("reads the policy and channel map from the secret, and survives a bad one", () => {
    const t = teamData(JSON.stringify({ policy: POLICY, channels: { _note: "x", "partner-x": "Supy" } }));
    expect(t.policy?.text).toBe("POLICY-TEXT-MARKER");
    expect(teamData(JSON.stringify({ policy: { text: " " } })).policy).toBeNull();
    expect(t.channels).toEqual({ "partner-x": "Supy" });
    expect(teamData("not json")).toEqual({ policy: null, channels: {} });
    expect(teamData(undefined)).toEqual({ policy: null, channels: {} });
  });
});

describe("data integrity", () => {
  it("every partner in a category has a profile and line items", () => {
    for (const c of CATEGORIES) for (const p of c.partners) {
      expect(PARTNERS[p], p).toBeDefined();
      expect(CATALOG[p]?.length, p).toBeGreaterThan(0);
    }
  });
  it("line items carry only list prices", () => {
    for (const items of Object.values(CATALOG)) for (const l of items) {
      expect(Object.keys(l).sort()).toEqual(expect.arrayContaining(["name", "p", "t", "f"]));
      for (const k of Object.keys(l)) expect(["name", "code", "desc", "p", "t", "f", "flag"]).toContain(k);
    }
  });
});

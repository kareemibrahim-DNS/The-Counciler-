import Anthropic from "@anthropic-ai/sdk";

export interface Turn {
  role: "user" | "assistant";
  content: string;
}

export interface AskOptions {
  apiKey: string;
  model: string;
  effort: "low" | "medium" | "high";
  stable: string; // cached system prefix
  audience: string; // per-channel rules + catalog slice
  turns: Turn[];
}

/** One Claude call. Returns the reply text, or a safe fallback line. */
export async function askClaude(o: AskOptions): Promise<string> {
  const client = new Anthropic({ apiKey: o.apiKey });
  const res = await client.beta.messages.create({
    model: o.model,
    max_tokens: 16000,
    betas: ["server-side-fallback-2026-07-01"],
    fallbacks: "default",
    output_config: { effort: o.effort },
    system: [
      { type: "text", text: o.stable, cache_control: { type: "ephemeral" } },
      { type: "text", text: o.audience },
    ],
    messages: o.turns,
  });

  if (res.stop_reason === "refusal") {
    return "I can't help with that one. Try rephrasing the question about a partner or a quote.";
  }
  const text = res.content
    .filter((b): b is Anthropic.Beta.BetaTextBlock => b.type === "text")
    .map((b) => b.text)
    .join("\n")
    .trim();
  return text || "I couldn't produce an answer. Please ask again.";
}

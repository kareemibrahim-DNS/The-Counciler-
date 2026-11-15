import { teamData } from "./data";
import { askClaude, type Turn } from "./llm";
import { asksForCost, audienceFor, COST_REFUSAL, EXTERNAL_REFUSAL } from "./policy";
import { buildSystem, relevantPartners } from "./prompt";
import { channelInfo, postReply, threadReplies, verifySlack } from "./slack";

export interface Env {
  SLACK_BOT_TOKEN: string;
  SLACK_SIGNING_SECRET: string;
  ANTHROPIC_API_KEY: string;
  CLAUDE_MODEL?: string; // default claude-opus-5-5
  CLAUDE_EFFORT?: "low" | "medium" | "high"; // default low: fast Slack replies
  POLICY_JSON?: string; // team-only discount policy and partner-channel map; never in the repo
}

interface SlackEvent {
  type: string;
  channel: string;
  channel_type?: string;
  text?: string;
  ts: string;
  thread_ts?: string;
  bot_id?: string;
  subtype?: string;
}

const MENTION = /<@[A-Z0-9]+>/g;

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);
    if (req.method !== "POST" || url.pathname !== "/slack/events") return new Response("Not found", { status: 404 });

    const body = await req.text();
    if (!(await verifySlack(req, body, env.SLACK_SIGNING_SECRET))) return new Response("Bad signature", { status: 401 });

    const payload = JSON.parse(body) as { type: string; challenge?: string; event?: SlackEvent };
    if (payload.type === "url_verification") return new Response(payload.challenge ?? "");

    // Slack retries if we're slow; the first delivery is already being handled.
    if (req.headers.get("x-slack-retry-num")) return new Response("ok");

    const ev = payload.event;
    const isMention = ev?.type === "app_mention";
    const isDm = ev?.type === "message" && ev.channel_type === "im" && !ev.subtype;
    if (ev && !ev.bot_id && (isMention || isDm)) ctx.waitUntil(handle(ev, env));
    return new Response("ok"); // ack within Slack's 3-second window
  },
};

async function handle(ev: SlackEvent, env: Env): Promise<void> {
  const threadTs = ev.thread_ts ?? ev.ts;
  try {
    const question = (ev.text ?? "").replace(MENTION, "").trim();
    if (!question) return postReply(env.SLACK_BOT_TOKEN, ev.channel, threadTs, "Ask me about a partner, a line item or a quote.");

    const team = teamData(env.POLICY_JSON);
    const audience = audienceFor(await channelInfo(env.SLACK_BOT_TOKEN, ev.channel), team.channels);
    if (audience.mode === "external") return postReply(env.SLACK_BOT_TOKEN, ev.channel, threadTs, EXTERNAL_REFUSAL);
    if (asksForCost(question)) return postReply(env.SLACK_BOT_TOKEN, ev.channel, threadTs, COST_REFUSAL);

    const turns = await threadTurns(env, ev, threadTs, question);
    const sel = relevantPartners(turns.filter((t) => t.role === "user").map((t) => t.content));
    const { stable, audience: audienceText } = buildSystem(audience, sel, team.policy);

    const answer = await askClaude({
      apiKey: env.ANTHROPIC_API_KEY,
      model: env.CLAUDE_MODEL || "claude-opus-5-5",
      effort: env.CLAUDE_EFFORT || "low",
      stable,
      audience: audienceText,
      turns,
    });
    await postReply(env.SLACK_BOT_TOKEN, ev.channel, threadTs, answer);
  } catch (err) {
    console.error(err);
    await postReply(env.SLACK_BOT_TOKEN, ev.channel, threadTs, "Something went wrong on my side. Please try again in a minute.").catch(() => {});
  }
}

/** Earlier messages in the thread become the conversation, oldest first, ending on the new question. */
async function threadTurns(env: Env, ev: SlackEvent, threadTs: string, question: string): Promise<Turn[]> {
  const turns: Turn[] = [];
  if (ev.thread_ts) {
    const msgs = await threadReplies(env.SLACK_BOT_TOKEN, ev.channel, threadTs);
    for (const m of msgs.slice(0, -1).slice(-10)) {
      const text = (m.text ?? "").replace(MENTION, "").trim();
      if (!text) continue;
      const role = m.bot_id ? "assistant" : "user";
      const last = turns[turns.length - 1];
      if (last && last.role === role) last.content += `\n${text}`;
      else turns.push({ role, content: text });
    }
    while (turns.length && turns[0].role !== "user") turns.shift();
  }
  const last = turns[turns.length - 1];
  if (last && last.role === "user") last.content += `\n${question}`;
  else turns.push({ role: "user", content: question });
  return turns;
}

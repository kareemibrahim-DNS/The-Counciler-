/** Minimal Slack Web API + request verification for Cloudflare Workers. */

const enc = new TextEncoder();

export async function verifySlack(req: Request, body: string, signingSecret: string): Promise<boolean> {
  const ts = req.headers.get("x-slack-request-timestamp");
  const sig = req.headers.get("x-slack-signature");
  if (!ts || !sig) return false;
  if (Math.abs(Date.now() / 1000 - Number(ts)) > 60 * 5) return false; // replay guard
  const key = await crypto.subtle.importKey("raw", enc.encode(signingSecret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const mac = await crypto.subtle.sign("HMAC", key, enc.encode(`v0:${ts}:${body}`));
  const hex = "v0=" + [...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, "0")).join("");
  return timingSafeEqual(hex, sig);
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}

async function api<T>(token: string, method: string, params: Record<string, unknown>): Promise<T> {
  const res = await fetch(`https://slack.com/api/${method}`, {
    method: "POST",
    headers: { authorization: `Bearer ${token}`, "content-type": "application/json; charset=utf-8" },
    body: JSON.stringify(params),
  });
  const json = (await res.json()) as T & { ok: boolean; error?: string };
  if (!json.ok) throw new Error(`Slack ${method} failed: ${json.error}`);
  return json;
}

export async function channelInfo(token: string, channel: string) {
  const r = await api<{ channel: { name?: string; is_im?: boolean; is_ext_shared?: boolean; is_shared?: boolean } }>(
    token, "conversations.info", { channel },
  );
  return {
    name: r.channel.name,
    isIm: !!r.channel.is_im,
    isExtShared: !!(r.channel.is_ext_shared || r.channel.is_shared),
  };
}

export interface SlackMsg {
  text?: string;
  bot_id?: string;
  user?: string;
}

export async function threadReplies(token: string, channel: string, ts: string): Promise<SlackMsg[]> {
  const r = await api<{ messages: SlackMsg[] }>(token, "conversations.replies", { channel, ts, limit: 20 });
  return r.messages;
}

export async function postReply(token: string, channel: string, threadTs: string, text: string) {
  await api(token, "chat.postMessage", { channel, thread_ts: threadTs, text, unfurl_links: false });
}

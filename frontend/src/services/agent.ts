// PLACEHOLDER for POST /ai/chat. Swap this for a real fetch once the FastAPI backend exists.
// The UI only depends on the AgentReply shape, so the swap should not touch components.

export type Proposal = { summary: string };
export type AgentReply = { text: string; proposal?: Proposal };

const amountRe = /(?:₦|n)?\s*(\d[\d,]*(?:\.\d+)?)\s*(k|thousand|m|million)?/gi;

function toNaira(raw: string): number | null {
  let best: number | null = null;
  for (const m of raw.matchAll(amountRe)) {
    let n = Number(m[1].replace(/,/g, ""));
    const unit = (m[2] ?? "").toLowerCase();
    if (unit === "k" || unit === "thousand") n *= 1_000;
    if (unit === "m" || unit === "million") n *= 1_000_000;
    if (unit || n >= 1000) best = n;
  }
  return best;
}

export async function sendToAgent(message: string): Promise<AgentReply> {
  const lower = message.toLowerCase();
  const amount = toNaira(message);
  const qty = lower.match(/(\d+)\s*(broilers?|birds?|chicks?|goats?|sheep|pigs?|rabbits?|cows?)/);

  if (/(sold|sell|sale)/.test(lower) && amount) {
    return { text: "I understood this as a sale. Should I save it?", proposal: { summary: `Sale${qty ? ` · ${qty[1]} ${qty[2]}` : ""} · ₦${amount.toLocaleString("en-NG")}` } };
  }
  if (/(bought|buy|purchase|spent|spend)/.test(lower) && amount) {
    const isFeed = /feed/.test(lower);
    return { text: "I understood this as a purchase. Should I save it?", proposal: { summary: `${isFeed ? "Feed expense" : "Purchase"}${qty ? ` · ${qty[1]} ${qty[2]}` : ""} · ₦${amount.toLocaleString("en-NG")}` } };
  }
  return { text: "I couldn't turn that into a farm record yet. Try: “I bought 100 broilers for 300k.”" };
}

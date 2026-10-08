import { api, backendConfigured } from "@/lib/api";

// Chat with Agro AI. Contract: docs/API_CONTRACT.md §1 (POST /chat/).
//
// With NEXT_PUBLIC_API_URL set this calls the real backend. Without it, a tiny demo parser answers so the
// UI can be shown offline. If a configured server fails, the error is shown to the farmer: we never hide an
// outage behind made-up answers.

export type Proposal = { summary: string };
export type AgentReply = { text: string; proposal?: Proposal };

type ChatResponse = { reply: string; session_id?: string; proposal?: Proposal };

export async function sendToAgent(message: string, sessionId: string): Promise<AgentReply> {
  if (!backendConfigured) return demoReply(message);

  const res = await api<ChatResponse>("/chat/", {
    method: "POST",
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  return { text: res.reply, proposal: res.proposal };
}

/** True when replies come from the built-in demo parser, not a server. */
export const isDemoAgent = !backendConfigured;

// ---------------------------------------------------------------------------------------------
// Demo parser (used only when no backend is configured)

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

function demoReply(message: string): AgentReply {
  const lower = message.toLowerCase();
  const amount = toNaira(message);
  const qty = lower.match(/(\d+)\s*(broilers?|birds?|chicks?|goats?|sheep|pigs?|rabbits?|cows?)/);

  if (/(sold|sell|sale)/.test(lower) && amount) {
    return {
      text: "I understood this as a sale. Should I save it?",
      proposal: { summary: `Sale${qty ? ` · ${qty[1]} ${qty[2]}` : ""} · ₦${amount.toLocaleString("en-NG")}` },
    };
  }
  if (/(bought|buy|purchase|spent|spend)/.test(lower) && amount) {
    const isFeed = /feed/.test(lower);
    return {
      text: "I understood this as a purchase. Should I save it?",
      proposal: {
        summary: `${isFeed ? "Feed expense" : "Purchase"}${qty ? ` · ${qty[1]} ${qty[2]}` : ""} · ₦${amount.toLocaleString("en-NG")}`,
      },
    };
  }
  return { text: "I couldn't turn that into a farm record yet. Try: “I bought 100 broilers for 300k.”" };
}

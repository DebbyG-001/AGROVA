import { api, backendConfigured } from "@/lib/api";
import { SPECIES, type HealthAssessment, type HealthForm, type RiskLevel } from "@/lib/health";

// Health assessment. Contract: docs/API_CONTRACT.md §2 (POST /health/assess).
//
// With NEXT_PUBLIC_API_URL set this calls the real backend. Without it, a few transparent rules pick a risk
// level and give only generic, safe first steps. The demo does NOT guess diseases: possibleConcerns stays
// empty on purpose. A configured server that fails shows its error; it never falls back to the demo rules.

type AssessResponse = {
  risk: RiskLevel;
  observed: string[];
  possible_concerns: string[];
  next_steps: string[];
  call_vet: string;
  photo_note?: string | null;
};

export async function assessHealth(f: HealthForm, photo: File | null): Promise<HealthAssessment> {
  if (!backendConfigured) return demoAssess(f, photo);

  const body = new FormData();
  body.append("species", f.species);
  body.append("symptoms", f.symptoms.trim());
  body.append("affected", f.affected);
  if (f.total) body.append("total", f.total);
  body.append("deaths", f.deaths);
  body.append("onset", f.onset);
  body.append("drinking", f.drinking);
  body.append("vaccinated", f.vaccinated);
  if (photo) body.append("photo", photo);

  const r = await api<AssessResponse>("/health/assess", { method: "POST", body });
  return {
    risk: r.risk,
    observed: r.observed ?? [],
    possibleConcerns: r.possible_concerns ?? [],
    nextSteps: r.next_steps ?? [],
    callVet: r.call_vet,
    source: "ai",
    photoNote: r.photo_note ?? undefined,
  };
}

// ---------------------------------------------------------------------------------------------
// Demo rules (used only when no backend is configured)

const RED_FLAGS = /breath|gasp|wheez|bloody|blood|seiz|paraly|can'?t stand|collaps|swollen head|sudden|twist|foam/i;

async function demoAssess(f: HealthForm, photo: File | null): Promise<HealthAssessment> {
  const affected = Number(f.affected);
  const total = f.total ? Number(f.total) : 0;
  const deaths = Number(f.deaths);
  const share = total > 0 ? affected / total : 0;
  const redFlag = RED_FLAGS.test(f.symptoms);

  let points = 0;
  if (deaths > 0) points += 2;
  if (deaths >= 3) points += 1;
  if (share >= 0.1) points += 1;
  if (share >= 0.3) points += 1;
  if (!total && affected >= 5) points += 1;
  if (redFlag) points += 2;
  if (f.drinking === "less") points += 1;
  if (f.onset === "today" && affected >= 3) points += 1;

  const risk: RiskLevel = points >= 4 ? "HIGH" : points >= 2 ? "MEDIUM" : "LOW";
  const animal = SPECIES.find((s) => s.key === f.species)?.label.toLowerCase() ?? "animals";

  const observed = [
    `${affected}${total ? ` of ${total}` : ""} ${animal} affected`,
    `Started: ${f.onset === "today" ? "today" : f.onset === "few-days" ? "2 to 3 days ago" : "a week or more ago"}`,
    deaths > 0 ? `${deaths} ${deaths === 1 ? "death" : "deaths"} reported` : "No deaths reported",
    f.drinking === "less" ? "Drinking less than normal" : "Drinking normally",
    `You described: "${f.symptoms.trim()}"`,
  ];

  const nextSteps = [
    "Separate the sick animals from the healthy ones.",
    "Make sure clean water and shade or shelter are available.",
    "Write down any new signs and how many are affected each day.",
    "Do not give medicines or home mixtures unless a vet or agro-vet tells you what and how much.",
  ];

  const callVet =
    risk === "HIGH"
      ? "Call a veterinarian today. If animals keep dying or breathing is difficult, report to your state veterinary office."
      : risk === "MEDIUM"
        ? "Call a veterinarian if more animals get sick, any die, or signs get worse in the next day or two."
        : "Call a veterinarian if signs get worse, spread to others, or any animal dies.";

  return {
    risk,
    observed,
    possibleConcerns: [],
    nextSteps,
    callVet,
    source: "demo",
    photoNote: photo
      ? "Your photo is attached but has not been analysed. Photo analysis needs Agro AI to be connected."
      : undefined,
  };
}

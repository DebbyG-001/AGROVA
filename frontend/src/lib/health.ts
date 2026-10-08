// Types + validation for the Health Assistant. Keep in sync with the backend health payload.

export const SPECIES = [
  { key: "poultry", label: "Poultry" },
  { key: "goats", label: "Goats" },
  { key: "sheep", label: "Sheep" },
  { key: "cattle", label: "Cattle" },
  { key: "pigs", label: "Pigs" },
  { key: "rabbits", label: "Rabbits" },
  { key: "fish", label: "Fish" },
] as const;

export const ONSET = [
  { key: "today", label: "Today", hint: "Started in the last day" },
  { key: "few-days", label: "2 to 3 days", hint: "Getting worse or steady" },
  { key: "week-plus", label: "A week or more", hint: "Has been going on a while" },
] as const;

export const DRINKING = [
  { key: "normal", label: "Drinking normally", hint: "Water intake looks fine" },
  { key: "less", label: "Drinking less", hint: "Or not drinking at all" },
] as const;

export const VACCINATED = [
  { key: "yes", label: "Yes", hint: "Recently vaccinated" },
  { key: "no", label: "No", hint: "Not recently" },
  { key: "unsure", label: "Not sure", hint: "I don't remember" },
] as const;

export type HealthForm = {
  species: string;
  symptoms: string;
  affected: string;
  total: string;
  deaths: string;
  onset: string;
  drinking: string;
  vaccinated: string;
};

export const emptyHealthForm: HealthForm = {
  species: "",
  symptoms: "",
  affected: "",
  total: "",
  deaths: "0",
  onset: "",
  drinking: "",
  vaccinated: "unsure",
};

export type HealthErrors = Partial<Record<keyof HealthForm | "photo", string>>;

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export type HealthAssessment = {
  risk: RiskLevel;
  /** What the farmer told us, echoed back so they can check it was understood. */
  observed: string[];
  possibleConcerns: string[];
  nextSteps: string[];
  callVet: string;
  /** "demo" = simple rules only, no AI. "ai" = produced by Agro AI. The UI labels demo results. */
  source: "demo" | "ai";
  photoNote?: string;
};

export const MAX_PHOTO_BYTES = 5 * 1024 * 1024;
export const PHOTO_TYPES = ["image/jpeg", "image/png", "image/webp"];

const WHOLE = /^\d{1,6}$/;

export function validateHealth(f: HealthForm, photo: File | null): HealthErrors {
  const e: HealthErrors = {};
  if (!f.species) e.species = "Choose the animal.";
  if (f.symptoms.trim().length < 5) e.symptoms = "Describe what you are seeing, even in a few words.";
  if (!WHOLE.test(f.affected) || Number(f.affected) < 1) e.affected = "Enter how many are affected (1 or more).";
  if (f.total && !WHOLE.test(f.total)) e.total = "Use a whole number.";
  else if (f.total && WHOLE.test(f.affected) && Number(f.affected) > Number(f.total))
    e.affected = "That is more than the group size you entered.";
  if (!WHOLE.test(f.deaths)) e.deaths = "Enter 0 if none have died.";
  if (!f.onset) e.onset = "Tell us when it started.";
  if (!f.drinking) e.drinking = "Tell us about their drinking.";
  if (photo) {
    if (!PHOTO_TYPES.includes(photo.type)) e.photo = "Use a JPG, PNG or WebP photo.";
    else if (photo.size > MAX_PHOTO_BYTES) e.photo = "That photo is over 5 MB. Try a smaller one.";
  }
  return e;
}

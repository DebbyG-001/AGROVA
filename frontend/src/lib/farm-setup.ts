// Shapes + options for the onboarding flow. Keep in sync with the backend farm/animal schema.

export const LIVESTOCK_TYPES = [
  { key: "poultry", label: "Poultry", hint: "Broilers, layers, turkeys" },
  { key: "goats", label: "Goats", hint: "Meat or dairy herds" },
  { key: "sheep", label: "Sheep", hint: "Rams, ewes, lambs" },
  { key: "cattle", label: "Cattle", hint: "Beef or dairy" },
  { key: "pigs", label: "Pigs", hint: "Sows, piglets, growers" },
  { key: "rabbits", label: "Rabbits", hint: "Meat or breeding" },
  { key: "fish", label: "Fish", hint: "Catfish, tilapia ponds" },
] as const;

export type LivestockKey = (typeof LIVESTOCK_TYPES)[number]["key"];

export const FARM_TYPES = [
  { key: "smallholder", label: "Smallholder", hint: "Family-run, a few animals to a few hundred" },
  { key: "commercial", label: "Commercial", hint: "Selling at scale, staff and records" },
  { key: "mixed", label: "Mixed", hint: "Different animals on one farm" },
  { key: "cooperative", label: "Cooperative", hint: "Run with other farmers" },
] as const;

export const FARM_SIZES = [
  { key: "small", label: "Small", hint: "Under 100 animals" },
  { key: "medium", label: "Medium", hint: "100 to 1,000 animals" },
  { key: "large", label: "Large", hint: "Over 1,000 animals" },
] as const;

export const NIGERIAN_STATES = [
  "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue", "Borno", "Cross River", "Delta",
  "Ebonyi", "Edo", "Ekiti", "Enugu", "FCT Abuja", "Gombe", "Imo", "Jigawa", "Kaduna", "Kano", "Katsina",
  "Kebbi", "Kogi", "Kwara", "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo", "Plateau",
  "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara",
];

export type FarmSetup = {
  ownerName: string;
  phone: string;
  farmName: string;
  location: string;
  farmType: string;
  size: string;
  /** A key is present when that livestock type is selected; the value is the optional head-count text. */
  livestock: Partial<Record<LivestockKey, string>>;
};

export const emptySetup: FarmSetup = {
  ownerName: "",
  phone: "",
  farmName: "",
  location: "",
  farmType: "",
  size: "",
  livestock: {},
};

export type Errors = Partial<Record<"ownerName" | "phone" | "farmName" | "location" | "farmType" | "size" | "livestock", string>>;

/** Nigerian mobile numbers: 0803 123 4567 or +234 803 123 4567. Optional, so empty is fine. */
const PHONE_RE = /^(?:\+?234|0)[789][01]\d{8}$/;

export function validateStep(step: number, s: FarmSetup): Errors {
  const e: Errors = {};
  if (step === 0) {
    if (s.ownerName.trim().length < 2) e.ownerName = "Please enter your name.";
    const phone = s.phone.replace(/[\s-]/g, "");
    if (phone && !PHONE_RE.test(phone)) e.phone = "Use a Nigerian number like 0803 123 4567.";
  }
  if (step === 1) {
    if (s.farmName.trim().length < 2) e.farmName = "Give your farm a name.";
    if (!s.location.trim()) e.location = "Tell us where your farm is.";
    if (!s.farmType) e.farmType = "Choose the kind of farm you run.";
    if (!s.size) e.size = "Choose roughly how big your farm is.";
  }
  if (step === 2) {
    const picked = Object.keys(s.livestock) as LivestockKey[];
    if (picked.length === 0) e.livestock = "Pick at least one kind of livestock.";
    else if (picked.some((k) => s.livestock[k] && !/^\d{1,6}$/.test(s.livestock[k] as string)))
      e.livestock = "Counts must be whole numbers.";
  }
  return e;
}

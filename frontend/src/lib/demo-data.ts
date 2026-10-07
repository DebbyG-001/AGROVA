// Demo data for Dons Farm. Replaced by API calls once the FastAPI backend is live.
// Keep shapes aligned with the backend schema (see Agrova spec §18).

export const farm = { name: "Dons Farm", location: "Ogun State, Nigeria" };

export const naira = (n: number) => `₦${n.toLocaleString("en-NG")}`;

export type LivestockGroup = { id: string; type: string; name: string; qty: number; status: "Healthy" | "Watch"; note: string };

export const livestock: LivestockGroup[] = [
  { id: "b001", type: "Poultry", name: "Broiler Batch 001", qty: 500, status: "Watch", note: "Mortality above baseline" },
  { id: "g001", type: "Goats", name: "Goat Herd 001", qty: 30, status: "Healthy", note: "Vaccination due tomorrow" },
  { id: "s001", type: "Sheep", name: "Sheep Herd 001", qty: 15, status: "Healthy", note: "No issues recorded" },
];

export const totals = {
  revenue: 1_240_000,
  expenses: 780_000,
  get profit() {
    return this.revenue - this.expenses;
  },
};

export const expenseBreakdown = [
  { category: "Feed", amount: 420_000 },
  { category: "Livestock purchases", amount: 200_000 },
  { category: "Medication", amount: 80_000 },
  { category: "Labour", amount: 50_000 },
  { category: "Transport", amount: 30_000 },
];

export type Severity = "INFO" | "LOW" | "WARNING" | "CRITICAL";

export const alerts: { id: string; severity: Severity; title: string; detail: string }[] = [
  {
    id: "a1",
    severity: "WARNING",
    title: "Mortality in Broiler Batch 001 is higher than its recent baseline",
    detail:
      "Review recent health observations, feed and water availability, and vaccination records. Consider contacting a veterinarian if mortality keeps rising.",
  },
  {
    id: "a2",
    severity: "INFO",
    title: "Vaccination due tomorrow: Goat Herd 001",
    detail: "A vaccination task is scheduled for tomorrow.",
  },
];

export const activity = ["Feed purchased · ₦80,000", "20 birds sold · ₦72,000", "Vaccination due · Goat Herd 001"];

export const quickActions = ["Record expense", "Check health", "View profit", "Add livestock", "Set reminder"];

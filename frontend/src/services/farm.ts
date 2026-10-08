import type { FarmSetup } from "@/lib/farm-setup";

// PLACEHOLDER for POST /farms. Stores the onboarding result in this browser only.
// Swap the body of saveFarm/loadFarm for real API calls once the backend has users + farms.
const KEY = "agrova.farm";

export async function saveFarm(setup: FarmSetup): Promise<void> {
  try {
    localStorage.setItem(KEY, JSON.stringify(setup));
  } catch {
    // Storage can be blocked (private mode); onboarding should still finish.
  }
}

export function loadFarm(): FarmSetup | null {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as FarmSetup) : null;
  } catch {
    return null;
  }
}

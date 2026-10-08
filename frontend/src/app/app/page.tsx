import Link from "next/link";
import { Button, Card, Tag } from "@/components/ui";
import { activity, alerts, farm, livestock, naira, totals } from "@/lib/demo-data";

export default function Dashboard() {
  const total = livestock.reduce((s, l) => s + l.qty, 0);
  const open = alerts.filter((a) => a.severity === "WARNING" || a.severity === "CRITICAL").length;
  return (
    <div className="space-y-5 lg:space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="label mb-2"><Tag>Good morning</Tag></p>
          <h1 className="h-display text-3xl lg:text-5xl">{farm.name}</h1>
        </div>
        <Button href="/app/ai" variant="forest" className="hidden lg:inline-flex !min-h-12 !px-7">
          Ask Agro AI
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4 lg:gap-4">
        <Stat label="Livestock" value={String(total)} />
        <Stat label="Revenue" value={naira(totals.revenue)} />
        <Stat label="Expenses" value={naira(totals.expenses)} />
        <Stat label="Est. profit" value={naira(totals.profit)} dark />
      </div>

      <div className="grid gap-5 lg:grid-cols-2 lg:gap-6">
        <div className="space-y-5">
          {open > 0 && (
            <Link
              href="/app/alerts"
              className="flex items-center justify-between rounded-2xl border border-warn/40 bg-white p-4"
            >
              <span className="font-bold text-warn">
                ⚠ {open} health alert{open > 1 ? "s" : ""}
              </span>
              <span className="label">View</span>
            </Link>
          )}
          <Card>
            <p className="label mb-3"><Tag>Today</Tag></p>
            <ul className="space-y-2">
              {activity.map((a) => (
                <li key={a} className="flex gap-2">
                  <span className="text-leaf">•</span>
                  {a}
                </li>
              ))}
            </ul>
          </Card>
        </div>

        <Card>
          <p className="label mb-3"><Tag>Livestock</Tag></p>
          <ul className="divide-y divide-forest/10">
            {livestock.map((l) => (
              <li key={l.id} className="flex items-center justify-between py-3">
                <span>
                  {l.name}
                  <span className="label ml-2 opacity-60">{l.type}</span>
                </span>
                <span className="font-mono">{l.qty}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <Link
        href="/app/health"
        className="flex items-center justify-between rounded-2xl border border-forest/10 bg-white p-4 lg:p-5"
      >
        <span>
          <span className="block font-bold">Check animal health</span>
          <span className="mt-1 block text-sm text-forest/75">Describe symptoms, get a risk level and next steps</span>
        </span>
        <span className="label ml-4 shrink-0">Open</span>
      </Link>

      <Button href="/app/ai" variant="forest" className="w-full !min-h-14 !text-base lg:hidden">
        Ask Agro AI
      </Button>
    </div>
  );
}

function Stat({ label, value, dark = false }: { label: string; value: string; dark?: boolean }) {
  return (
    <div className={`rounded-2xl p-4 lg:p-6 ${dark ? "bg-forest text-lime" : "bg-white border border-forest/10"}`}>
      <p className="label opacity-70">{label}</p>
      <p className="mt-2 font-mono text-xl lg:text-3xl">{value}</p>
    </div>
  );
}

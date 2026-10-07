import Link from "next/link";
import { Button, Card, Tag } from "@/components/ui";
import { activity, alerts, farm, livestock, naira, totals } from "@/lib/demo-data";

export default function Dashboard() {
  const total = livestock.reduce((s, l) => s + l.qty, 0);
  const open = alerts.filter((a) => a.severity === "WARNING" || a.severity === "CRITICAL").length;
  return (
    <div className="space-y-5">
      <div>
        <p className="label"><Tag>Good morning</Tag></p>
        <h1 className="h-display text-3xl">{farm.name}</h1>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Stat label="Livestock" value={String(total)} />
        <Stat label="Revenue" value={naira(totals.revenue)} />
        <Stat label="Expenses" value={naira(totals.expenses)} />
        <Stat label="Est. profit" value={naira(totals.profit)} dark />
      </div>

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

      <Button href="/app/ai" variant="forest" className="w-full !min-h-14 !text-base">
        Ask Agrova AI
      </Button>
    </div>
  );
}

function Stat({ label, value, dark = false }: { label: string; value: string; dark?: boolean }) {
  return (
    <div className={`rounded-2xl p-4 ${dark ? "bg-forest text-lime" : "bg-white border border-forest/10"}`}>
      <p className="label opacity-70">{label}</p>
      <p className="mt-2 font-mono text-xl">{value}</p>
    </div>
  );
}

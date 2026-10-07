import { Card } from "@/components/ui";
import { alerts, type Severity } from "@/lib/demo-data";

const tone: Record<Severity, string> = {
  INFO: "bg-mist text-forest",
  LOW: "bg-lime text-forest",
  WARNING: "bg-warn/15 text-warn",
  CRITICAL: "bg-critical/15 text-critical",
};

export default function Alerts() {
  return (
    <div className="space-y-4">
      <h1 className="h-display text-3xl lg:text-5xl">Alerts</h1>
      {alerts.length === 0 ? (
        <Card>All clear. Agrova will alert you if something looks unusual.</Card>
      ) : (
        <ul className="grid gap-3 lg:grid-cols-2 lg:gap-4">
          {alerts.map((a) => (
            <li key={a.id}>
              <Card>
                <span className={`label rounded-full px-3 py-1 ${tone[a.severity]}`}>{a.severity}</span>
                <h2 className="mt-3 font-bold">{a.title}</h2>
                <p className="mt-2 text-sm text-forest/80">{a.detail}</p>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

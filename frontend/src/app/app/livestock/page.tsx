import { Card, Tag } from "@/components/ui";
import { livestock } from "@/lib/demo-data";

export default function Livestock() {
  return (
    <div className="space-y-4">
      <h1 className="h-display text-3xl lg:text-5xl">Livestock</h1>
      {livestock.length === 0 ? (
        <Card>No livestock yet. Tell Agrova what you bought and it will be added.</Card>
      ) : (
        <ul className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 lg:gap-4">
          {livestock.map((l) => (
            <li key={l.id}>
              <Card>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="label"><Tag>{l.type}</Tag></p>
                    <h2 className="mt-2 text-lg font-bold">{l.name}</h2>
                  </div>
                  <span className="font-mono text-2xl">{l.qty}</span>
                </div>
                <p className="mt-3 flex items-center gap-2 text-sm">
                  <span
                    className={`label rounded-full px-3 py-1 ${
                      l.status === "Healthy" ? "bg-lime" : "bg-warn/15 text-warn"
                    }`}
                  >
                    {l.status}
                  </span>
                  {l.note}
                </p>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

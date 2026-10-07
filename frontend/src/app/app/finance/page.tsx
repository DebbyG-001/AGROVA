import { Card, Tag } from "@/components/ui";
import { expenseBreakdown, naira, totals } from "@/lib/demo-data";

export default function Finance() {
  const sum = expenseBreakdown.reduce((s, e) => s + e.amount, 0);
  const margin = Math.round((totals.profit / totals.revenue) * 100);
  return (
    <div className="space-y-4">
      <h1 className="h-display text-3xl">Finance</h1>
      <div className="rounded-2xl bg-forest p-5 text-lime">
        <p className="label opacity-70">Estimated profit</p>
        <p className="mt-2 font-mono text-3xl">{naira(totals.profit)}</p>
        <p className="label mt-2">{margin}% margin · from recorded data</p>
      </div>
      <Card>
        <p className="label mb-4"><Tag>Expense breakdown</Tag></p>
        <ul className="space-y-4">
          {expenseBreakdown.map((e) => {
            const pct = Math.round((e.amount / sum) * 100);
            return (
              <li key={e.category}>
                <div className="mb-1 flex justify-between text-sm">
                  <span>{e.category}</span>
                  <span className="font-mono">
                    {naira(e.amount)} · {pct}%
                  </span>
                </div>
                <div className="h-2 rounded-full bg-mist" role="img" aria-label={`${e.category} ${pct}%`}>
                  <div className="h-2 rounded-full bg-leaf" style={{ width: `${pct}%` }} />
                </div>
              </li>
            );
          })}
        </ul>
      </Card>
    </div>
  );
}

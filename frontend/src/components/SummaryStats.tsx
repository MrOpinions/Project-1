import type { AffectedOrder } from "@/lib/types"

function Stat({ value, label }: { value: string | number; label: string }) {
  return (
    <div className="rounded-lg border bg-card p-3 text-center">
      <div className="font-mono text-xl font-bold">{value}</div>
      <div className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</div>
    </div>
  )
}

export function SummaryStats({
  orders,
  unresolvedCount,
}: {
  orders: AffectedOrder[]
  unresolvedCount: number
}) {
  const slips = orders.map((o) => o.slip_days).filter((s): s is number => s !== null)
  const slipRange = slips.length
    ? `${Math.min(...slips)}-${Math.max(...slips)}d`
    : "unquantified"
  const top = orders[0]

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <Stat value={orders.length} label="Orders affected" />
      <Stat value={slipRange} label="Slip range" />
      <Stat value={top ? top.order_id : "-"} label="Most urgent" />
      <Stat value={unresolvedCount} label="Unresolved mentions" />
    </div>
  )
}

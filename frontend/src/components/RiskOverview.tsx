import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { TIER_BG, TIER_LABEL } from "@/lib/severity"
import type { AffectedOrder, SeverityTier } from "@/lib/types"
import { urgencyTier } from "@/lib/types"
import { cn } from "@/lib/utils"

const LEGEND_TIERS: SeverityTier[] = ["critical", "high", "medium", "low"]

export function RiskOverview({ orders }: { orders: AffectedOrder[] }) {
  const maxScore = Math.max(...orders.map((o) => o.urgency_score))

  return (
    <Card>
      <CardHeader>
        <CardTitle>Risk overview</CardTitle>
        <CardDescription>
          Orders ranked by urgency - longer, redder bars need attention first.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex flex-wrap gap-4 text-xs text-muted-foreground">
          {LEGEND_TIERS.map((tier) => (
            <span key={tier} className="inline-flex items-center gap-1.5">
              <span className={cn("inline-block size-2.5 rounded-full", TIER_BG[tier])} />
              {TIER_LABEL[tier]}
            </span>
          ))}
        </div>
        <div className="flex flex-col gap-1.5">
          {orders.map((o) => {
            const tier = urgencyTier(o.urgency_score)
            const pct = Math.max(4, Math.round((o.urgency_score / maxScore) * 100))
            const slip = o.slip_days === null ? "unquantified" : `${o.slip_days}d late`
            return (
              <div key={o.order_id} className="grid grid-cols-[90px_1fr_80px] items-center gap-3 py-1">
                <span className="truncate font-mono text-sm">{o.order_id}</span>
                <div className="h-4 overflow-hidden rounded-sm bg-status-track">
                  <div
                    className={cn("h-full min-w-1 rounded-sm", TIER_BG[tier])}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className="text-right text-xs tabular-nums text-muted-foreground">{slip}</span>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { SeverityMeter } from "@/components/SeverityMeter"
import { TIER_BORDER, TIER_LABEL } from "@/lib/severity"
import type { ActionOption, AffectedOrder } from "@/lib/types"
import { urgencyTier } from "@/lib/types"
import { cn } from "@/lib/utils"
import { ArrowLeftRight, Mail, PackageOpen, Zap } from "lucide-react"

const OPTION_ICON: Record<string, React.ComponentType<{ className?: string }>> = {
  expedite: Zap,
  part_ship: PackageOpen,
  reallocate: ArrowLeftRight,
  notify_customer: Mail,
}

const TIER_BADGE_VARIANT: Record<string, string> = {
  vip: "bg-foreground text-background",
  priority: "bg-secondary text-secondary-foreground",
  standard: "bg-muted text-muted-foreground",
}

function Option({ option, isRecommended }: { option: ActionOption; isRecommended: boolean }) {
  const Icon = OPTION_ICON[option.kind] ?? Zap
  return (
    <div
      className={cn(
        "rounded-md border p-3 text-sm",
        isRecommended ? "border-foreground/40 bg-foreground/5" : "border-border",
      )}
    >
      <div className="mb-1 flex items-center gap-2 font-medium capitalize">
        <Icon className="size-3.5" />
        {option.kind.replace("_", " ")}
        {isRecommended && (
          <Badge variant="secondary" className="uppercase">
            Recommended
          </Badge>
        )}
      </div>
      <p>{option.description}</p>
      <p className="mt-1 text-xs italic text-muted-foreground">Trade-off: {option.trade_off}</p>
    </div>
  )
}

export function OrderCard({ order, maxScore }: { order: AffectedOrder; maxScore: number }) {
  const tier = urgencyTier(order.urgency_score)
  const slip = order.slip_days === null ? "unquantified" : `${order.slip_days}d slip`

  return (
    <Card className={cn("border-l-4", TIER_BORDER[tier])}>
      <CardHeader>
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-base font-bold">{order.order_id}</span>
          <Badge className={TIER_BADGE_VARIANT[order.tier] ?? ""}>{order.tier}</Badge>
          <Badge variant="outline" className="ml-auto uppercase">
            {TIER_LABEL[tier]}
          </Badge>
        </div>
        <SeverityMeter score={order.urgency_score} maxScore={maxScore} tier={tier} className="mt-1" />
        <p className="text-sm text-muted-foreground">
          {order.customer} &middot; {order.quantity}&times; {order.product} &middot; due{" "}
          {order.requested_delivery_date} &middot; {slip}
        </p>
        <p className="font-mono text-xs text-muted-foreground/70">
          source: {order.source_ids.join(", ")}
        </p>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        {order.options.map((opt, i) => (
          <Option key={opt.kind} option={opt} isRecommended={i === order.recommended_index} />
        ))}
      </CardContent>
    </Card>
  )
}

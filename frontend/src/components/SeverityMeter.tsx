import { TIER_BG } from "@/lib/severity"
import type { SeverityTier } from "@/lib/types"
import { cn } from "@/lib/utils"

export function SeverityMeter({
  score,
  maxScore,
  tier,
  className,
}: {
  score: number
  maxScore: number
  tier: SeverityTier
  className?: string
}) {
  const pct = Math.max(4, Math.round((score / maxScore) * 100))
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-status-track">
        <div
          className={cn("h-full rounded-full", TIER_BG[tier])}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs tabular-nums text-muted-foreground">{score}</span>
    </div>
  )
}

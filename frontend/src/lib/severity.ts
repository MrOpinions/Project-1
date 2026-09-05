import type { SeverityTier } from "./types"

export const TIER_LABEL: Record<SeverityTier, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
}

export const TIER_BG: Record<SeverityTier, string> = {
  critical: "bg-status-critical",
  high: "bg-status-serious",
  medium: "bg-status-warning",
  low: "bg-status-good",
}

export const TIER_TEXT: Record<SeverityTier, string> = {
  critical: "text-status-critical",
  high: "text-status-serious",
  medium: "text-status-warning",
  low: "text-status-good",
}

export const TIER_BORDER: Record<SeverityTier, string> = {
  critical: "border-l-status-critical",
  high: "border-l-status-serious",
  medium: "border-l-status-warning",
  low: "border-l-status-good",
}

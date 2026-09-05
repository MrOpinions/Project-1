export interface ResolvedEntity {
  mention: string
  entity_key: string | null
  score: number
  method: string
}

export interface ActionOption {
  kind: string
  description: string
  trade_off: string
  new_estimate: string | null
}

export interface AffectedOrder {
  order_id: string
  customer: string
  tier: string
  product: string
  quantity: number
  requested_delivery_date: string
  exposure_kind: string
  source_ids: string[]
  original_ready_date: string | null
  revised_ready_date: string | null
  slip_days: number | null
  urgency_score: number
  options: ActionOption[]
  recommended_index: number
}

export type NarrativeStatus =
  | "grounded"
  | "rejected_hallucination"
  | "rejected_unavailable"
  | "deterministic"

export interface AnalyzeResponse {
  no_impact: boolean
  disruption_type: string
  notice_summary: string
  narrative: string
  narrative_status: NarrativeStatus
  narrative_cited_ids: string[]
  resolved_entities: ResolvedEntity[]
  unresolved_mentions: string[]
  affected_orders: AffectedOrder[]
}

export interface AnalyzeError {
  error: string
  detail?: string
}

export interface SampleNotice {
  title: string
  text: string
}

export type SeverityTier = "critical" | "high" | "medium" | "low"

export function urgencyTier(score: number): SeverityTier {
  if (score >= 100) return "critical"
  if (score >= 60) return "high"
  if (score >= 30) return "medium"
  return "low"
}

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import type { NarrativeStatus } from "@/lib/types"
import { CheckCircle2, TriangleAlert } from "lucide-react"

const COPY: Partial<Record<NarrativeStatus, { label: (n: number) => string }>> = {
  grounded: {
    label: (n) => `${n}/${n} claims verified against source data`,
  },
  rejected_hallucination: {
    label: () =>
      "AI narrative cited an unverified reference and was replaced with computer-verified facts",
  },
  rejected_unavailable: {
    label: () => "AI narrative was unavailable; showing computer-verified facts instead",
  },
}

export function GroundingCheck({
  status,
  citedIds,
}: {
  status: NarrativeStatus
  citedIds: string[]
}) {
  const spec = COPY[status]
  if (!spec) return null // "deterministic" - no-impact case, no AI narrative to check

  const grounded = status === "grounded"

  return (
    <Alert
      className={
        grounded
          ? "mt-3 border-status-good/35 bg-status-good/10 text-status-good [&>svg]:text-status-good"
          : "mt-3 border-status-warning/35 bg-status-warning/10 text-status-warning [&>svg]:text-status-warning"
      }
    >
      {grounded ? <CheckCircle2 className="size-4" /> : <TriangleAlert className="size-4" />}
      <AlertTitle>{spec.label(citedIds.length)}</AlertTitle>
      {citedIds.length > 0 && (
        <AlertDescription className="font-mono text-current/80">
          {citedIds.join(", ")}
        </AlertDescription>
      )}
    </Alert>
  )
}

import { useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import { GroundingCheck } from "@/components/GroundingCheck"
import { OrderCard } from "@/components/OrderCard"
import { RiskOverview } from "@/components/RiskOverview"
import { SummaryStats } from "@/components/SummaryStats"
import { analyzeNotice, fetchSamples } from "@/lib/api"
import type { AnalyzeResponse, SampleNotice } from "@/lib/types"

export default function Workspace() {
  const [notice, setNotice] = useState("")
  const [samples, setSamples] = useState<SampleNotice[]>([])
  const [selectedSample, setSelectedSample] = useState<string>("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const resultRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchSamples().then(setSamples)
  }, [])

  useEffect(() => {
    if (result || error) {
      resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }, [result, error])

  async function analyze() {
    const text = notice.trim()
    if (!text) return
    setLoading(true)
    setError(null)
    setResult(null)
    const outcome = await analyzeNotice(text)
    if (outcome.ok) {
      setResult(outcome.data)
    } else {
      setError(outcome.error)
    }
    setLoading(false)
  }

  function clearAll() {
    setNotice("")
    setSelectedSample("")
    setResult(null)
    setError(null)
  }

  function onSampleChange(value: string | null) {
    if (value === null) return
    setSelectedSample(value)
    const sample = samples[Number(value)]
    if (sample) setNotice(sample.text)
  }

  const maxScore = result ? Math.max(...result.affected_orders.map((o) => o.urgency_score), 1) : 1

  return (
    <div className="min-h-screen bg-background text-foreground">
      <nav className="flex items-center justify-between border-b px-6 py-3">
        <a href="/" className="flex items-center gap-2 font-semibold">
          <img src="/logo-light.png" alt="" className="size-6 opacity-90" />
          Disruption Response Assistant
        </a>
        <a href="/" className="text-sm text-muted-foreground hover:text-foreground">
          Overview
        </a>
      </nav>

      <div className="mx-auto max-w-3xl px-6 pb-16 pt-8">
        <header className="mb-6">
          <h1 className="text-2xl font-bold">Impact Workspace</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Paste a disruption notice as it actually arrives. The system maps it to your data, traces
            the impact, and proposes an action plan. It does not act on its own.
          </p>
        </header>

        <Card>
          <CardContent className="pt-6">
            <Textarea
              value={notice}
              onChange={(e) => setNotice(e.target.value)}
              onKeyDown={(e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === "Enter") analyze()
              }}
              placeholder="Paste a supplier email, carrier delay notice, or warehouse incident report here..."
              className="min-h-36"
              aria-label="Disruption notice text"
            />
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Select value={selectedSample} onValueChange={onSampleChange}>
                <SelectTrigger className="w-64" aria-label="Load a sample notice">
                  <SelectValue placeholder="Load a sample notice...">
                    {(value: string | null) =>
                      value ? samples[Number(value)]?.title : "Load a sample notice..."
                    }
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {samples.map((s, i) => (
                    <SelectItem key={s.title} value={String(i)}>
                      {s.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button variant="outline" onClick={clearAll} type="button">
                Clear
              </Button>
              <Button onClick={analyze} disabled={loading}>
                Analyze
              </Button>
              <span className="ml-auto text-xs text-muted-foreground">Ctrl+Enter to analyze</span>
            </div>
          </CardContent>
        </Card>

        <div ref={resultRef} className="mt-8 scroll-mt-6">
          {loading && (
            <div className="flex flex-col items-center gap-3 py-10 text-sm text-muted-foreground">
              <Skeleton className="h-8 w-8 rounded-full" />
              <p>Extracting notice, resolving entities, tracing impact...</p>
            </div>
          )}

          {!loading && error && (
            <Card className="border-destructive/40 bg-destructive/10">
              <CardContent className="pt-6 text-sm text-destructive">{error}</CardContent>
            </Card>
          )}

          {!loading && !error && !result && (
            <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
              No notice analyzed yet. Paste one above, or load a sample, then press Analyze.
            </div>
          )}

          {!loading && !error && result && (
            <div className="flex flex-col gap-4">
              <Card className={result.no_impact ? "border-l-4 border-l-status-good" : "border-l-4 border-l-status-warning"}>
                <CardHeader>
                  <CardTitle className="text-sm uppercase tracking-wide">
                    {result.no_impact ? "No impact" : "Impact assessment"}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-relaxed">{result.narrative}</p>
                  <GroundingCheck status={result.narrative_status} citedIds={result.narrative_cited_ids} />
                </CardContent>
              </Card>

              {!result.no_impact && result.affected_orders.length > 0 && (
                <>
                  <RiskOverview orders={result.affected_orders} />
                  <SummaryStats orders={result.affected_orders} unresolvedCount={result.unresolved_mentions.length} />
                </>
              )}

              {(result.resolved_entities.length > 0 || result.unresolved_mentions.length > 0) && (
                <details className="rounded-lg border p-3 text-sm text-muted-foreground">
                  <summary className="cursor-pointer font-medium text-foreground">
                    Entity resolution ({result.resolved_entities.length})
                  </summary>
                  <ul className="mt-2 list-disc space-y-1 pl-5">
                    {result.resolved_entities.map((r, i) => (
                      <li key={i}>
                        "{r.mention}" &rarr; {r.entity_key ?? "no confident match"} ({r.method}, score{" "}
                        {r.score})
                      </li>
                    ))}
                  </ul>
                </details>
              )}

              {!result.no_impact && (
                <div className="flex flex-col gap-4">
                  {result.affected_orders.map((o) => (
                    <OrderCard key={o.order_id} order={o} maxScore={maxScore} />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

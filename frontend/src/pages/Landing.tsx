import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

const FEATURES = [
  {
    title: "Grounded, not guessed",
    body: "Every claim traces back to a specific purchase order, shipment, or stock lot ID in the data.",
  },
  {
    title: "Built for a small model",
    body: "All impact math runs as deterministic Python. The AI only reads notices and writes summaries.",
  },
  {
    title: "No impact is an answer",
    body: "If nothing pending is actually exposed, it says so, instead of manufacturing a story.",
  },
]

const STEPS = [
  {
    n: "1",
    title: "Paste the notice",
    body: "A supplier email, carrier delay, or warehouse report, exactly as it arrived.",
  },
  {
    n: "2",
    title: "Trace the real chain",
    body: "Supplier to purchase order to shipment to stock to customer order, deterministically.",
  },
  {
    n: "3",
    title: "Get ranked actions",
    body: "Affected orders ranked by urgency, each with options and a recommendation.",
  },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <nav className="flex items-center justify-between border-b px-6 py-3">
        <a href="/" className="flex items-center gap-2 font-semibold">
          <img src="/logo-light.png" alt="" className="size-6 opacity-90" />
          Disruption Response Assistant
        </a>
        <Button render={<a href="/app" />} size="sm">
          Open Workspace
        </Button>
      </nav>

      <main className="mx-auto max-w-5xl px-6 pb-20">
        <section className="max-w-2xl pb-14 pt-24">
          <h1 className="text-4xl font-bold leading-[1.15] tracking-tight sm:text-5xl">
            See what a disruption actually breaks.
          </h1>
          <p className="mt-4 max-w-xl text-lg text-muted-foreground">
            Paste a supplier delay or warehouse incident. Get the exact orders at risk, how late, and
            what to do next.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Button render={<a href="/app" />} size="lg">
              Open Workspace
            </Button>
            <Button
              render={<a href="https://github.com/MrOpinions/Project-1" target="_blank" rel="noopener" />}
              size="lg"
              variant="outline"
            >
              View source
            </Button>
          </div>
        </section>

        <section className="grid gap-4 border-t py-10 sm:grid-cols-3">
          {FEATURES.map((f) => (
            <Card key={f.title}>
              <CardContent className="pt-6">
                <h3 className="mb-1.5 font-semibold">{f.title}</h3>
                <p className="text-sm text-muted-foreground">{f.body}</p>
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="grid gap-6 border-t py-10 sm:grid-cols-3">
          {STEPS.map((s) => (
            <div key={s.n} className="flex gap-3">
              <span className="text-lg font-bold text-foreground/70">{s.n}</span>
              <div>
                <h4 className="mb-1 text-sm font-semibold">{s.title}</h4>
                <p className="text-sm text-muted-foreground">{s.body}</p>
              </div>
            </div>
          ))}
        </section>
      </main>

      <footer className="mx-auto flex max-w-5xl items-center justify-between border-t px-6 py-6 text-sm text-muted-foreground">
        <span>Built for NexusTiQ 24 - CareerTiQ, Supply Chain track (PS08)</span>
        <a href="https://github.com/MrOpinions/Project-1" target="_blank" rel="noopener" className="hover:text-foreground">
          GitHub
        </a>
      </footer>
    </div>
  )
}

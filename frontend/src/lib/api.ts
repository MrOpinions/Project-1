import type { AnalyzeError, AnalyzeResponse, SampleNotice } from "./types"

export async function fetchSamples(): Promise<SampleNotice[]> {
  const res = await fetch("/api/samples")
  return res.json()
}

export async function analyzeNotice(
  notice: string,
): Promise<{ ok: true; data: AnalyzeResponse } | { ok: false; error: string }> {
  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notice }),
    })
    const data = await res.json()
    if (!res.ok) {
      const err = data as AnalyzeError
      return { ok: false, error: err.error || "Request failed." }
    }
    return { ok: true, data: data as AnalyzeResponse }
  } catch (e) {
    return { ok: false, error: `Something went wrong: ${String(e)}` }
  }
}

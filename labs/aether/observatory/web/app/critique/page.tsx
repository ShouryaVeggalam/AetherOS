"use client";

import { useCallback, useState } from "react";

type CritiqueResponse = {
  id: string;
  overall: number;
  verdict: string;
  scores: { criterion: string; score: number; notes: string }[];
};

const API_BASE =
  process.env.NEXT_PUBLIC_AETHER_API ?? "http://127.0.0.1:8000";

export default function CritiquePage() {
  const [summary, setSummary] = useState(
    "Therefore the strategic plan holds because evidence supports the architecture boundaries.",
  );
  const [result, setResult] = useState<CritiqueResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const cog = await fetch(`${API_BASE}/aether/cognition`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          objective: "Strategic system architecture with evidence protocol",
          priority: 75,
        }),
      });
      if (!cog.ok) throw new Error(`cognition HTTP ${cog.status}`);
      const bundle = (await cog.json()) as { plan: { id: string } };
      const res = await fetch(`${API_BASE}/aether/critique`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan_id: bundle.plan.id,
          reasoning_summary: summary,
          evidence: ["paper-1", "telemetry-baseline", "prior-architecture"],
        }),
      });
      if (!res.ok) throw new Error(`critique HTTP ${res.status}`);
      setResult((await res.json()) as CritiqueResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "request failed");
    } finally {
      setLoading(false);
    }
  }, [summary]);

  return (
    <section className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold">Critique</h2>
        <p className="mt-2 max-w-2xl text-aether-mute">
          Structured self-evaluation — correctness, completeness, consistency,
          evidence quality, confidence calibration. Module 4.
        </p>
      </div>
      <div className="rounded-lg border border-white/10 bg-aether-panel p-5">
        <textarea
          className="w-full rounded-md border border-white/10 bg-aether-bg px-3 py-2 font-mono text-sm"
          rows={4}
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
        />
        <button
          type="button"
          onClick={run}
          disabled={loading}
          className="mt-4 rounded-md bg-aether-accent px-4 py-2 text-sm font-medium text-aether-bg disabled:opacity-50"
        >
          {loading ? "Critiquing…" : "Run Critique"}
        </button>
        {error ? (
          <p className="mt-3 font-mono text-sm text-red-400">{error}</p>
        ) : null}
      </div>
      {result ? (
        <div className="space-y-4">
          <p className="font-mono text-sm">
            Verdict <span className="text-aether-accent">{result.verdict}</span> ·
            overall {(result.overall * 100).toFixed(0)}%
          </p>
          <ul className="space-y-3">
            {result.scores.map((s) => (
              <li
                key={s.criterion}
                className="grid grid-cols-[10rem_1fr_3rem] items-center gap-3"
              >
                <span className="font-mono text-xs">{s.criterion}</span>
                <div className="h-3 overflow-hidden rounded-sm bg-white/5">
                  <div
                    className="h-full bg-gradient-to-r from-aether-accent to-aether-heat"
                    style={{ width: `${s.score * 100}%` }}
                  />
                </div>
                <span className="font-mono text-xs text-aether-mute">
                  {s.score.toFixed(2)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

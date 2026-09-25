"use client";

import { useCallback, useState } from "react";

type AttentionResponse = {
  id: string;
  goal_id: string;
  signals: {
    task_complexity: number;
    available_context: number;
    memory_relevance: number;
    uncertainty: number;
  };
  weights: Record<string, number>;
  reasoning_budget: number;
  retrieval_budget: number;
  factors: string[];
  confidence: number;
};

const API_BASE =
  process.env.NEXT_PUBLIC_AETHER_API ?? "http://127.0.0.1:8000";

const CHANNELS = ["focus", "memory", "exploration", "verification"] as const;

export default function AttentionMapPage() {
  const [objective, setObjective] = useState(
    "Design a hierarchical research plan under uncertain evidence",
  );
  const [data, setData] = useState<AttentionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/aether/attention`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          objective,
          priority: 75,
          constraints: ["explainable", "deterministic"],
          context: { memory_relevance: 0.6 },
        }),
      });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const json = (await res.json()) as AttentionResponse;
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : "request failed");
    } finally {
      setLoading(false);
    }
  }, [objective]);

  const maxW = data
    ? Math.max(...CHANNELS.map((c) => data.weights[c] ?? 0), 0.01)
    : 1;

  return (
    <section className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold">Attention Map</h2>
        <p className="mt-2 max-w-2xl text-aether-mute">
          Adaptive attention allocation across focus, memory, exploration, and
          verification. Deterministic · explainable · Module 1.
        </p>
      </div>

      <div className="rounded-lg border border-white/10 bg-aether-panel p-5">
        <label className="block text-sm text-aether-mute" htmlFor="objective">
          Objective
        </label>
        <textarea
          id="objective"
          className="mt-2 w-full rounded-md border border-white/10 bg-aether-bg px-3 py-2 font-mono text-sm"
          rows={3}
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
        />
        <button
          type="button"
          onClick={run}
          disabled={loading}
          className="mt-4 rounded-md bg-aether-accent px-4 py-2 text-sm font-medium text-aether-bg disabled:opacity-50"
        >
          {loading ? "Allocating…" : "Allocate Attention"}
        </button>
        {error ? (
          <p className="mt-3 font-mono text-sm text-red-400">{error}</p>
        ) : null}
      </div>

      {data ? (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-3">
            <Stat label="Confidence" value={`${(data.confidence * 100).toFixed(0)}%`} />
            <Stat
              label="Reasoning budget"
              value={data.reasoning_budget.toFixed(2)}
            />
            <Stat
              label="Retrieval budget"
              value={data.retrieval_budget.toFixed(2)}
            />
          </div>

          <div className="rounded-lg border border-white/10 bg-aether-panel p-5">
            <h3 className="mb-4 text-sm uppercase tracking-widest text-aether-mute">
              Channel heatmap
            </h3>
            <ul className="space-y-3">
              {CHANNELS.map((channel) => {
                const w = data.weights[channel] ?? 0;
                const pct = (w / maxW) * 100;
                return (
                  <li key={channel} className="grid grid-cols-[7rem_1fr_3rem] items-center gap-3">
                    <span className="font-mono text-sm capitalize">{channel}</span>
                    <div className="h-3 overflow-hidden rounded-sm bg-white/5">
                      <div
                        className="h-full rounded-sm bg-gradient-to-r from-aether-accent to-aether-heat"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="font-mono text-xs text-aether-mute">
                      {w.toFixed(2)}
                    </span>
                  </li>
                );
              })}
            </ul>
          </div>

          <div className="rounded-lg border border-white/10 bg-aether-panel p-5">
            <h3 className="mb-3 text-sm uppercase tracking-widest text-aether-mute">
              Factors
            </h3>
            <ul className="space-y-1 font-mono text-xs text-aether-mute">
              {data.factors.map((f) => (
                <li key={f}>· {f}</li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-aether-panel px-4 py-3">
      <p className="text-xs uppercase tracking-widest text-aether-mute">{label}</p>
      <p className="mt-1 font-mono text-xl">{value}</p>
    </div>
  );
}

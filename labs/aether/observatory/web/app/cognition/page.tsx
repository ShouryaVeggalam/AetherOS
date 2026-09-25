"use client";

import { useCallback, useState } from "react";

type Bundle = {
  goal_id: string;
  plan: {
    id: string;
    complexity: string;
    confidence: number;
    stages: { name: string; description: string; attention_share: number }[];
  };
  task_graph: { id: string; tasks: unknown[] };
  attention: { id: string; reasoning_budget: number };
};

const API_BASE =
  process.env.NEXT_PUBLIC_AETHER_API ?? "http://127.0.0.1:8000";

export default function CognitionPage() {
  const [objective, setObjective] = useState(
    "Build explainable hierarchical cognition for research systems",
  );
  const [bundle, setBundle] = useState<Bundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/aether/cognition`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ objective, priority: 70, max_depth: 3 }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setBundle((await res.json()) as Bundle);
    } catch (err) {
      setError(err instanceof Error ? err.message : "request failed");
    } finally {
      setLoading(false);
    }
  }, [objective]);

  return (
    <section className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold">Cognition</h2>
        <p className="mt-2 max-w-2xl text-aether-mute">
          Attention → Decomposition → Hierarchical Plan. Cognition replay via
          plan stages.
        </p>
      </div>
      <div className="rounded-lg border border-white/10 bg-aether-panel p-5">
        <textarea
          className="w-full rounded-md border border-white/10 bg-aether-bg px-3 py-2 font-mono text-sm"
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
          {loading ? "Running…" : "Run Cognition"}
        </button>
        {error ? (
          <p className="mt-3 font-mono text-sm text-red-400">{error}</p>
        ) : null}
      </div>
      {bundle ? (
        <div className="space-y-4">
          <p className="font-mono text-xs text-aether-mute">
            plan {bundle.plan.id} · {bundle.plan.complexity} · conf{" "}
            {(bundle.plan.confidence * 100).toFixed(0)}% · graph{" "}
            {bundle.task_graph.tasks.length} tasks
          </p>
          <ol className="space-y-2">
            {bundle.plan.stages.map((s, i) => (
              <li
                key={s.name}
                className="rounded-md border border-white/10 bg-aether-panel px-4 py-3"
              >
                <span className="font-mono text-xs text-aether-mute">
                  {i + 1}. {s.name}
                </span>
                <p className="text-sm">{s.description}</p>
              </li>
            ))}
          </ol>
        </div>
      ) : null}
    </section>
  );
}

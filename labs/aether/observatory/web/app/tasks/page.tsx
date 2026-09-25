"use client";

import { useCallback, useState } from "react";

type Task = {
  id: string;
  type: string;
  depth: number;
  statement: string;
  dependencies: string[];
  status: string;
};

type GraphResponse = {
  id: string;
  objective: string;
  tasks: Task[];
  roots: string[];
  max_depth: number;
  topo_order: string[];
};

const API_BASE =
  process.env.NEXT_PUBLIC_AETHER_API ?? "http://127.0.0.1:8000";

export default function TasksPage() {
  const [objective, setObjective] = useState(
    "Design a hierarchical research architecture under uncertain evidence",
  );
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/aether/decompose`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          objective,
          priority: 80,
          max_depth: 4,
          constraints: ["explainable", "deterministic"],
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setGraph((await res.json()) as GraphResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "request failed");
    } finally {
      setLoading(false);
    }
  }, [objective]);

  return (
    <section className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold">Task Graph</h2>
        <p className="mt-2 max-w-2xl text-aether-mute">
          Hierarchical DAG — Strategic → Tactical → Operational → Execution.
          Module 2 Decomposition Engine.
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
          {loading ? "Decomposing…" : "Decompose"}
        </button>
        {error ? (
          <p className="mt-3 font-mono text-sm text-red-400">{error}</p>
        ) : null}
      </div>

      {graph ? (
        <div className="space-y-4">
          <p className="font-mono text-xs text-aether-mute">
            {graph.tasks.length} nodes · depth {graph.max_depth} · id {graph.id}
          </p>
          <ul className="space-y-2">
            {graph.tasks.map((task) => (
              <li
                key={task.id}
                className="rounded-md border border-white/10 bg-aether-panel px-4 py-3"
                style={{ marginLeft: `${task.depth * 1.25}rem` }}
              >
                <div className="flex items-center gap-3 text-xs uppercase tracking-widest text-aether-mute">
                  <span>{task.type}</span>
                  <span>{task.status}</span>
                </div>
                <p className="mt-1 text-sm">{task.statement}</p>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

"use client";

import { useCallback, useState } from "react";

type CognitionBundle = {
  goal_id: string;
  plan: { id: string; complexity: string; confidence: number };
};

type ReflectionResponse = {
  id: string;
  weaknesses: string[];
  assumptions: string[];
  improvements: string[];
  revised_plan: { id: string; status: string } | null;
};

const API_BASE =
  process.env.NEXT_PUBLIC_AETHER_API ?? "http://127.0.0.1:8000";

export default function ReflectionPage() {
  const [summary, setSummary] = useState(
    "We assume the architecture is scalable because prior systems worked. Maybe evidence is incomplete.",
  );
  const [result, setResult] = useState<ReflectionResponse | null>(null);
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
          objective: "Strategic system architecture research under uncertainty",
          priority: 80,
          max_depth: 3,
        }),
      });
      if (!cog.ok) throw new Error(`cognition HTTP ${cog.status}`);
      const bundle = (await cog.json()) as CognitionBundle;
      const res = await fetch(`${API_BASE}/aether/reflect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan_id: bundle.plan.id,
          reasoning_summary: summary,
          evidence: [],
          revise: true,
        }),
      });
      if (!res.ok) throw new Error(`reflect HTTP ${res.status}`);
      setResult((await res.json()) as ReflectionResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "request failed");
    } finally {
      setLoading(false);
    }
  }, [summary]);

  return (
    <section className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold">Reflection</h2>
        <p className="mt-2 max-w-2xl text-aether-mute">
          Assumption explorer and improvement timeline — Module 3.
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
          {loading ? "Reflecting…" : "Run Reflection"}
        </button>
        {error ? (
          <p className="mt-3 font-mono text-sm text-red-400">{error}</p>
        ) : null}
      </div>
      {result ? (
        <div className="grid gap-4 md:grid-cols-3">
          <List title="Weaknesses" items={result.weaknesses} />
          <List title="Assumptions" items={result.assumptions} />
          <List title="Improvements" items={result.improvements} />
          {result.revised_plan ? (
            <p className="font-mono text-xs text-aether-mute md:col-span-3">
              Revised plan {result.revised_plan.id} · {result.revised_plan.status}
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function List({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-lg border border-white/10 bg-aether-panel p-4">
      <h3 className="text-xs uppercase tracking-widest text-aether-mute">{title}</h3>
      <ul className="mt-3 space-y-2 font-mono text-xs">
        {items.length === 0 ? (
          <li className="text-aether-mute">(none)</li>
        ) : (
          items.map((item) => <li key={item}>· {item}</li>)
        )}
      </ul>
    </div>
  );
}

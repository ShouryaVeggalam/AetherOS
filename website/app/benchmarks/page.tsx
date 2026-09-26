import type { Metadata } from "next";
import Link from "next/link";
import { DocsCta, Feature, PageHero, Section } from "@/components/PageChrome";

export const metadata: Metadata = {
  title: "Benchmarks",
  description: "Score the system, not the vibes — AetherOS benchmark posture.",
};

export default function BenchmarksPage() {
  return (
    <>
      <PageHero
        eyebrow="Evaluation"
        title="Score the system, not the vibes."
        lede="Benchmarks target attention allocation, plan feasibility, critique recall, and provenance completeness. Leaderboard chat scores are out of scope."
      />
      <Section title="Suites" copy="Named suites ship with CELESTRA research lineage and an open harness — do not invent marketing numbers.">
        <div className="grid-2">
          <Feature title="Attention" body="Budget adherence under competing goals." />
          <Feature title="Decomposition" body="Task-graph fidelity vs gold hierarchies." />
          <Feature title="Critique" body="Recall of seeded material faults before accept." />
          <Feature title="Provenance" body="Percent of answers with resolvable citations." />
        </div>
      </Section>
      <Section title="Reporting" copy="Results publish as versioned artifacts — reproducible inputs, pinned stack versions, no silent prompt edits.">
        <div className="grid-3">
          <Feature title="Format" body="JSON + human summary in Observatory." />
          <Feature title="Compare" body="Diff runs across AetherOS versions." />
          <Feature title="Private" body="Enterprise suites stay in-tenant." />
        </div>
        <div className="cta-row">
          <Link className="btn btn-solid btn-lg" href="/open-source">
            Run the open harness
          </Link>
        </div>
      </Section>
      <DocsCta />
    </>
  );
}

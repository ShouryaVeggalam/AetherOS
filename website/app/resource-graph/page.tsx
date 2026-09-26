import type { Metadata } from "next";
import Link from "next/link";
import { DocsCta, Feature, PageHero, Section } from "@/components/PageChrome";

export const metadata: Metadata = {
  title: "Resource Graph",
  description: "AetherOS Resource Graph — models, tools, memory, and budgets as a living topology.",
};

export default function ResourceGraphPage() {
  return (
    <>
      <PageHero
        eyebrow="Topology"
        title="Every capability is a node."
        lede="The Resource Graph maps models, tools, memory stores, and attention budgets. Scheduling and cognition route through topology — not ad-hoc function lists."
      />
      <Section title="Why a graph" copy="Lists do not capture contention. Graphs do. When two plans compete for the same encoder, the scheduler sees the edge.">
        <div className="grid-2">
          <Feature title="Nodes" body="Models, tools, corpora, twin instances, human approvers." />
          <Feature title="Edges" body="Affinity, denial, cost, latency, residency constraints." />
          <Feature title="Policy" body="Read-only edges cannot promote to write without a new grant." />
          <Feature title="Operator view" body="Inspect hot paths, starved nodes, and policy blocks before a cognition run commits budget." />
        </div>
      </Section>
      <Section title="Graph facets" copy="Same underlying store — multiple projections.">
        <div className="grid-4">
          <Feature title="Capacity heatmap" body="Where budgets concentrate." />
          <Feature title="Policy overlay" body="Deny and residency edges." />
          <Feature title="Cost projection" body="Edge-weighted spend foresight." />
          <Feature title="Residency map" body="Region and tenancy constraints." />
        </div>
        <div className="cta-row">
          <Link className="btn btn-solid btn-lg" href="/digital-twin">
            Mirror the world you run
          </Link>
        </div>
      </Section>
      <DocsCta />
    </>
  );
}

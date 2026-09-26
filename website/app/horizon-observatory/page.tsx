import type { Metadata } from "next";
import Link from "next/link";
import { DocsCta, Feature, PageHero, Section } from "@/components/PageChrome";

export const metadata: Metadata = {
  title: "Horizon Observatory",
  description: "Horizon Observatory — see every thought that mattered.",
};

export default function HorizonObservatoryPage() {
  return (
    <>
      <PageHero
        eyebrow="System of record"
        title="See every thought that mattered."
        lede="Horizon Observatory turns cognition into operational truth: timelines, traces, critique outcomes, and connector health — without burying operators in dashboards."
      />
      <Section title="What you see" copy="One job per surface. Sparse metrics. Full provenance.">
        <div className="grid-3">
          <Feature title="Run timeline" body="Ordered cognition events." />
          <Feature title="Attention map" body="Where budget was spent." />
          <Feature title="Task graph" body="Decomposition you can audit." />
          <Feature title="Plan inspector" body="Feasible steps and blockers." />
          <Feature title="Reflection / critique" body="Faults caught before accept." />
          <Feature title="Connector health" body="Read-only ingress status." />
        </div>
      </Section>
      <Section title="Audit posture" copy="Investors and security teams get the same artifact engineers use — not a separate marketing view.">
        <div className="grid-3">
          <Feature title="IDs" body="Request IDs and cognition run IDs on every path." />
          <Feature title="Export" body="PDF / CSV under customer export policy." />
          <Feature title="Retention" body="Pilot default: term + 30 days, then delete or return." />
        </div>
        <div className="cta-row">
          <Link className="btn btn-solid btn-lg" href="/benchmarks">
            Measure what you claim
          </Link>
        </div>
      </Section>
      <DocsCta />
    </>
  );
}

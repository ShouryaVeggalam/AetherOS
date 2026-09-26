import type { Metadata } from "next";
import Link from "next/link";
import { DocsCta, Feature, PageHero, Section } from "@/components/PageChrome";

export const metadata: Metadata = {
  title: "Digital Twin",
  description: "AetherOS Digital Twin — simulated environments without writing production.",
};

export default function DigitalTwinPage() {
  return (
    <>
      <PageHero
        eyebrow="Simulation"
        title="Rehearse before reality."
        lede="Digital Twin environments let AetherOS plan and critique against faithful replicas. Production systems stay read-only until humans promote a change."
      />
      <Section title="Twin contract" copy="A twin is versioned state plus transition rules. Cognition runs inside the twin; Observatory records what would have happened.">
        <div className="grid-2">
          <Feature title="State" body="Snapshots from approved exports or streaming read replicas." />
          <Feature title="Transitions" body="Simulated writes confined to twin storage — never live SoR." />
          <Feature title="Fidelity" body="Declare drift budgets; fail closed when twin skew exceeds limit." />
          <Feature title="Promotion" body="Human-gated export of plans — not automatic actuation." />
        </div>
      </Section>
      <Section title="Enterprise fit" copy="Regulated teams get rehearsal without risk. The twin is where critique earns its keep.">
        <div className="grid-3">
          <Feature title="Incident twin" body="Replay sanitized alerts into postmortem cognition." />
          <Feature title="Capacity twin" body="Stress scheduler decisions against synthetic load." />
          <Feature title="Policy twin" body="Validate residency and deny-lists before live connectors widen." />
        </div>
        <div className="cta-row">
          <Link className="btn btn-solid btn-lg" href="/global-knowledge-graph">
            Knowledge that compounds
          </Link>
        </div>
      </Section>
      <DocsCta />
    </>
  );
}

import type { Metadata } from "next";
import Link from "next/link";
import { DocsCta, Feature, PageHero, Section } from "@/components/PageChrome";

export const metadata: Metadata = {
  title: "Planetary Scheduler",
  description: "AetherOS Planetary Scheduler — global placement advice under policy.",
};

export default function PlanetarySchedulerPage() {
  return (
    <>
      <PageHero
        eyebrow="Time + capacity"
        title="Schedule cognition like infrastructure."
        lede="The Planetary Scheduler allocates attention windows, model capacity, and human review slots across regions — respecting residency, cost, and deadlines."
      />
      <Section title="Scheduling inputs" copy="Not a cron wrapper. A planner that reads the Resource Graph and emits feasible windows — simulation-only advice.">
        <div className="grid-2">
          <Feature title="Demand" body="Cognition goals with deadlines and priority classes." />
          <Feature title="Supply" body="Model capacity, tool quotas, twin availability." />
          <Feature title="Constraints" body="Region locks, maintenance blackouts, human-in-loop SLAs." />
          <Feature title="Output" body="Top-N windows + deferrals with explicit reasons." />
        </div>
      </Section>
      <Section title="Operator guarantees" copy="Missed windows are visible. Starved queues page humans. Silent drops are defects.">
        <div className="grid-3">
          <Feature title="Fairness" body="Priority classes with starvation detection." />
          <Feature title="Explain" body="Every deferral cites the binding constraint." />
          <Feature title="Pilot" body="Schedules observation jobs only — no mutating jobs." />
        </div>
        <div className="cta-row">
          <Link className="btn btn-solid btn-lg" href="/horizon-observatory">
            Horizon Observatory
          </Link>
        </div>
      </Section>
      <DocsCta />
    </>
  );
}

import type { Metadata } from "next";
import Link from "next/link";
import { DocsCta, Feature, PageHero, Section } from "@/components/PageChrome";

export const metadata: Metadata = {
  title: "Architecture",
  description: "AetherOS architecture — intelligence core, Horizon layer, Observatory.",
};

export default function ArchitecturePage() {
  return (
    <>
      <PageHero
        eyebrow="System"
        title="Precision layers. Visible seams."
        lede="AetherOS separates experience, cognition, platform, and data. Each layer has a contract. Nothing important hides behind a single prompt."
        actions={
          <Link className="btn btn-solid btn-lg" href="/open-source">
            Open source
          </Link>
        }
      />
      <Section
        title="Reference stack"
        copy="The intelligence core observes and explains. Horizon adds federation, twins, global graph, and planetary advice. Observatory surfaces are Rich — never actuators."
      >
        <div className="grid-2">
          <Feature title="Experience · Dashboard / Observatory" body="Rich operator surfaces and aetheros-horizon." />
          <Feature title="Horizon · Cloud · Twin · Graph · Scheduler" body="v6 planetary observation and advice." />
          <Feature title="Intelligence · Graph · Reasoning · Twin" body="Evidence-backed recommendations only." />
          <Feature title="Operating · Telemetry · Policy · Safety" body="Userspace, read-only, human-in-the-loop." />
        </div>
      </Section>
      <Section title="Runtime" copy="Bootable on a developer workstation. Health and coverage gates are first-class.">
        <div className="grid-4">
          <Feature title="API" body="FastAPI · Python 3.12+ · /api/v1" />
          <Feature title="UI" body="Rich terminal · Horizon Observatory" />
          <Feature title="Safety" body="No shell / kubectl / Terraform apply" />
          <Feature title="Pilot mode" body="Read-only connectors and twin sandboxes" />
        </div>
        <div className="cta-row">
          <Link className="btn btn-solid btn-lg" href="/resource-graph">
            Follow the resource graph
          </Link>
        </div>
      </Section>
      <DocsCta />
    </>
  );
}

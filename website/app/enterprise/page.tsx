import type { Metadata } from "next";
import Link from "next/link";
import { DocsCta, Feature, PageHero, Section } from "@/components/PageChrome";

export const metadata: Metadata = {
  title: "Enterprise",
  description: "Enterprise pilots for AetherOS — read-only by default.",
};

export default function EnterprisePage() {
  return (
    <>
      <PageHero
        eyebrow="First customer kit"
        title="Enterprise pilots. Read-only."
        lede="Eight weeks. Customer VPC or dedicated tenant. Up to three read-only connectors. Two cognition use cases. Zero writes to systems of record."
        actions={
          <Link className="btn btn-solid btn-lg" href="/open-source">
            Prefer open source first?
          </Link>
        }
      />
      <Section title="Pilot shape" copy="Commercial, security, deploy, and ROI artifacts ship as a single kit.">
        <div className="grid-2">
          <Feature title="Duration" body="8 weeks + exit / conversion window" />
          <Feature title="Seats" body="≤ 25 Observatory users" />
          <Feature title="Security" body="Questionnaire + gates before ingest" />
          <Feature title="Success" body="≥ 3 of 5 scorecard metrics; zero policy violations" />
          <Feature title="SLA" body="99.0% pilot availability · business-hours SEV response" />
          <Feature title="Exit" body="Export artifacts · revoke credentials · wipe staging" />
        </div>
      </Section>
      <Section title="Topology" copy="Choose control vs speed — both remain single-tenant.">
        <div className="grid-2">
          <Feature title="Option A" body="Customer VPC — preferred for regulated data" />
          <Feature title="Option B" body="CELESTRA dedicated tenant — faster start" />
        </div>
        <div className="cta-row">
          <Link className="btn btn-solid btn-lg" href="/research">
            Research program
          </Link>
        </div>
      </Section>
      <DocsCta />
    </>
  );
}

import type { Metadata } from "next";
import Link from "next/link";
import { DocsCta, Feature, PageHero, Section } from "@/components/PageChrome";

export const metadata: Metadata = {
  title: "Problem",
  description: "Foundation models infer. They are not an operating system for intelligence.",
};

export default function ProblemPage() {
  return (
    <>
      <PageHero
        eyebrow="The gap"
        title="Models infer. Systems still guess."
        lede="Enterprises bolted chat onto workflows and called it intelligence. What they needed was infrastructure: attention budgets, plans you can audit, memory with provenance, and critique before action."
      />
      <Section
        title="What broke"
        copy="Agent frameworks optimized for demos. Prompt chains evaporate under compliance. There is no system of record for cognition — only transcripts."
      >
        <div className="grid-2">
          <Feature title="Opacity" body="Reasoning cannot be inspected, versioned, or underwritten." />
          <Feature title="Drift" body="Every team invents a different agent stack with no shared primitives." />
          <Feature title="Risk" body="Write-happy automations touch production without a critique gate." />
          <Feature title="Cost" body="Unbounded tool use burns tokens without an attention economy." />
        </div>
      </Section>
      <Section
        title="What AetherOS changes"
        copy="Treat cognition as an operating system. Allocate attention. Decompose. Plan. Reflect. Critique. Persist the trace. Run it in your boundary — read-only until you choose otherwise."
      >
        <div className="grid-3">
          <Feature title="Primitive" body="Cognition runs with explicit schemas — not freeform chat." />
          <Feature title="Boundary" body="Enterprise pilots start read-only against systems of record." />
          <Feature title="Surface" body="Horizon Observatory turns every run into an auditable artifact." />
        </div>
        <div className="cta-row">
          <Link className="btn btn-solid btn-lg" href="/architecture">
            See the architecture
          </Link>
        </div>
      </Section>
      <DocsCta />
    </>
  );
}

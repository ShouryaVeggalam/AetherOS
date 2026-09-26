import type { Metadata } from "next";
import Link from "next/link";
import { DocsCta, Feature, PageHero, Section } from "@/components/PageChrome";

export const metadata: Metadata = {
  title: "Research",
  description: "CELESTRA X research lineage behind AetherOS.",
};

export default function ResearchPage() {
  return (
    <>
      <PageHero
        eyebrow="CELESTRA X"
        title="From lab to infrastructure."
        lede="AetherOS inherits a research program: attention, decomposition, planning, reflection, critique, and observatory modules — RFC to prototype to benchmark to paper."
      />
      <Section title="Program stance" copy="Not a product pitch deck. A governed path from ideas to runnable systems.">
        <div className="grid-2">
          <Feature title="RFC" body="Immutable proposals with review state." />
          <Feature title="Labs" body="Aether cognition · Atlas · Chronicle · Nexus and more." />
          <Feature title="Benchmark" body="Named suites before narrative claims." />
          <Feature title="Paper" body="Artifacts generated from experiments, not the reverse." />
        </div>
      </Section>
      <Section title="Aether lineage" copy="Foundation models perform inference. Aether performs cognition — the executive system AetherOS operationalizes.">
        <div className="grid-3">
          <Feature title="M1" body="Attention Engine" />
          <Feature title="M2" body="Decomposition" />
          <Feature title="M3" body="Hierarchical Planning" />
          <Feature title="M4" body="Reflection" />
          <Feature title="M5" body="Critique" />
          <Feature title="M6–7" body="Orchestrator · Observatory" />
        </div>
        <div className="cta-row">
          <Link className="btn btn-solid btn-lg" href="/problem">
            Read the problem
          </Link>
          <Link className="btn btn-outline btn-lg" href="/enterprise">
            Request pilot
          </Link>
        </div>
      </Section>
      <DocsCta />
    </>
  );
}

import type { Metadata } from "next";
import Link from "next/link";
import { DocsCta, Feature, PageHero, Section } from "@/components/PageChrome";

export const metadata: Metadata = {
  title: "Global Knowledge Graph",
  description: "AetherOS Global Knowledge Graph — provenance-first memory across sources.",
};

export default function GlobalKnowledgeGraphPage() {
  return (
    <>
      <PageHero
        eyebrow="Memory"
        title="Knowledge with edges, not piles."
        lede="The Global Knowledge Graph unifies documents, events, and twin state under typed relations. Retrieval is attention-ranked and always citeable."
      />
      <Section title="Graph primitives" copy="Entities, claims, sources, and temporal validity. No orphan embeddings pretending to be truth.">
        <div className="grid-3">
          <Feature title="Entity" body="Named things with stable IDs." />
          <Feature title="Claim" body="Asserted facts with confidence." />
          <Feature title="Source" body="Evidence operators can open." />
          <Feature title="Relation" body="Typed edges between entities." />
          <Feature title="Time window" body="Validity intervals, not eternal truth." />
          <Feature title="Policy tag" body="Residency and disclosure constraints." />
        </div>
      </Section>
      <Section title="Provenance rules" copy="Every answer path must resolve to sources the operator can open. Missing provenance fails the run.">
        <div className="grid-3">
          <Feature title="Ingest" body="Read-only connectors + document exports only." />
          <Feature title="Rank" body="Attention engine scores relevance under a budget." />
          <Feature title="Cite" body="Observatory shows the path: claim → source → connector." />
        </div>
        <div className="cta-row">
          <Link className="btn btn-solid btn-lg" href="/planetary-scheduler">
            Planetary Scheduler
          </Link>
        </div>
      </Section>
      <DocsCta />
    </>
  );
}

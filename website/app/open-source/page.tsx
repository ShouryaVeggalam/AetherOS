import type { Metadata } from "next";
import Link from "next/link";
import { DocsCta, Feature, PageHero, Section } from "@/components/PageChrome";
import { site } from "@/lib/site";

export const metadata: Metadata = {
  title: "Open Source",
  description:
    "AetherOS open source — MIT-licensed explainable operating intelligence on GitHub.",
};

export default function OpenSourcePage() {
  return (
    <>
      <PageHero
        eyebrow="Builders"
        title="Clone. Compose. Inspect."
        lede={`${site.name} is open on GitHub under MIT: userspace telemetry, resource graphs, twins, planetary placement advice, and Rich observatories — read-only and human-in-the-loop.`}
        actions={
          <>
            <a
              className="btn btn-solid btn-lg"
              href={site.github.repoUrl}
              rel="noreferrer"
              target="_blank"
            >
              GitHub
            </a>
            <Link className="btn btn-outline btn-lg" href="/architecture">
              Architecture
            </Link>
          </>
        }
      />

      <Section
        title="What ships open"
        copy="Start from the public repository. Horizon pillars and the intelligence core ship with docs, tests, and contribution guides."
      >
        <div className="grid-3">
          <Feature
            title={site.github.repoName}
            body="Python package · Rich dashboard · Horizon Observatory · FastAPI /api/v1"
          />
          <Feature
            title="www"
            body="This flagship site — Next.js + CSS, deployable from /website"
          />
          <Feature
            title="Contracts"
            body="Installation · CELESTRA charter · SECURITY.md · read-only pilot stance"
          />
        </div>
      </Section>

      <Section title="Local boot" copy="Production-shaped from minute one — no privileged OS mutation required.">
        <div className="panel panel-mono" role="region" aria-label="Install commands">
          {site.install.join("\n")}
        </div>
        <div className="cta-row">
          <a
            className="btn btn-solid btn-lg"
            href={site.github.repoUrl}
            rel="noreferrer"
            target="_blank"
          >
            Open {site.github.owner}/{site.github.repoName}
          </a>
          <a
            className="btn btn-outline btn-lg"
            href={`${site.github.repoUrl}#readme`}
            rel="noreferrer"
            target="_blank"
          >
            README
          </a>
        </div>
      </Section>

      <Section
        title="Need a governed pilot?"
        copy="Enterprise kits are read-only by default."
      >
        <div className="cta-row">
          <Link className="btn btn-solid btn-lg" href="/enterprise">
            Enterprise
          </Link>
        </div>
      </Section>

      <DocsCta />
    </>
  );
}

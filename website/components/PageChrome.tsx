import type { ReactNode } from "react";
import Link from "next/link";

export function PageHero({
  eyebrow,
  title,
  lede,
  actions,
}: {
  eyebrow: string;
  title: string;
  lede: string;
  actions?: ReactNode;
}) {
  return (
    <section className="page-hero">
      <div className="container">
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="lede">{lede}</p>
        {actions ? <div className="cta-row">{actions}</div> : null}
      </div>
    </section>
  );
}

export function Section({
  title,
  copy,
  children,
}: {
  title: string;
  copy?: string;
  children?: ReactNode;
}) {
  return (
    <section className="section">
      <div className="container">
        <h2>{title}</h2>
        {copy ? <p className="section-copy">{copy}</p> : null}
        {children}
      </div>
    </section>
  );
}

export function Feature({ title, body }: { title: string; body: string }) {
  return (
    <div className="feature">
      <h3>{title}</h3>
      <p>{body}</p>
    </div>
  );
}

export function DocsCta() {
  return (
    <section className="section">
      <div className="container">
        <h2>Prefer docs first?</h2>
        <p className="section-copy">Explore open source</p>
        <div className="cta-row">
          <Link className="btn btn-solid btn-lg" href="/open-source">
            Open Source
          </Link>
          <Link className="btn btn-outline btn-lg" href="/architecture">
            Architecture
          </Link>
        </div>
      </div>
    </section>
  );
}

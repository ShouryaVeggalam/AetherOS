import Link from "next/link";
import { site } from "@/lib/site";

export default function HomePage() {
  return (
    <section className="home-hero">
      <div className="home-hero-bg" aria-hidden="true" />
      <div className="container home-hero-inner">
        <p className="eyebrow">{site.org}</p>
        <h1>{site.name}</h1>
        <p className="lede">{site.tagline}</p>
        <div className="cta-row">
          <Link className="btn btn-solid btn-lg" href="/architecture">
            View architecture
          </Link>
          <Link className="btn btn-outline btn-lg" href="/enterprise">
            Enterprise pilot
          </Link>
        </div>
      </div>
    </section>
  );
}

import Link from "next/link";
import { footerProduct, navSecondary, site } from "@/lib/site";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="container footer-grid">
        <div>
          <h2>{site.name}</h2>
          <p>
            {site.tagline}. Built by {site.org}.
          </p>
        </div>
        <div className="footer-col">
          <p className="footer-col-label">Product</p>
          <ul>
            {footerProduct.map((item) => (
              <li key={item.href}>
                <Link href={item.href}>{item.label}</Link>
              </li>
            ))}
          </ul>
        </div>
        <div className="footer-col">
          <p className="footer-col-label">Company</p>
          <ul>
            {navSecondary.map((item) => (
              <li key={item.href}>
                <Link href={item.href}>{item.label}</Link>
              </li>
            ))}
            <li>
              <a href={site.github.repoUrl} rel="noreferrer" target="_blank">
                GitHub
              </a>
            </li>
          </ul>
        </div>
      </div>
      <div className="footer-bar">
        <div className="container footer-bar">
          <span>
            © {new Date().getFullYear()} {site.org}
          </span>
          <span className="font-mono" style={{ letterSpacing: "0.16em", textTransform: "uppercase" }}>
            Read-only pilots available
          </span>
        </div>
      </div>
    </footer>
  );
}

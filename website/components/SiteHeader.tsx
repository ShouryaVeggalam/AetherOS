"use client";

import Link from "next/link";
import { useState } from "react";
import { navPrimary, navSecondary, site } from "@/lib/site";

export function SiteHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className="site-header">
      <div className="container site-header-inner">
        <Link className="brand" href="/">
          {site.name}
          <span className="hidden-sm">{site.org}</span>
        </Link>

        <nav className="nav-primary" aria-label="Product">
          {navPrimary.map((item) => (
            <Link key={item.href} className="nav-link" href={item.href}>
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="nav-secondary">
          {navSecondary.map((item) => (
            <Link key={item.href} className="nav-link" href={item.href}>
              {item.label}
            </Link>
          ))}
          <Link className="btn btn-solid" href="/enterprise">
            Request pilot
          </Link>
        </div>

        <button
          type="button"
          className="menu-btn"
          aria-expanded={open}
          aria-controls="mobile-nav"
          onClick={() => setOpen((v) => !v)}
        >
          Menu
        </button>
      </div>

      <div id="mobile-nav" className={`mobile-nav${open ? " open" : ""}`}>
        {[...navPrimary, ...navSecondary].map((item) => (
          <Link
            key={item.href}
            className="nav-link"
            href={item.href}
            onClick={() => setOpen(false)}
          >
            {item.label}
          </Link>
        ))}
        <Link className="btn btn-solid" href="/enterprise" onClick={() => setOpen(false)}>
          Request pilot
        </Link>
      </div>
    </header>
  );
}

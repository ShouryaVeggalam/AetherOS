import type { Metadata } from "next";
import { IBM_Plex_Mono, Manrope, Syne } from "next/font/google";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { site } from "@/lib/site";
import "./globals.css";

const syne = Syne({
  subsets: ["latin"],
  variable: "--font-display-loaded",
  display: "swap",
});

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-body-loaded",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono-loaded",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: `${site.name} · ${site.org}`,
    template: `%s · ${site.name}`,
  },
  description: site.description,
  openGraph: {
    title: `${site.name} · ${site.tagline}`,
    description: site.description,
    siteName: site.name,
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${syne.variable} ${manrope.variable} ${plexMono.variable}`}>
        <style>{`
          :root {
            --font-display: var(--font-display-loaded), "Avenir Next", sans-serif;
            --font-body: var(--font-body-loaded), "Avenir Next", sans-serif;
            --font-mono: var(--font-mono-loaded), ui-monospace, monospace;
          }
          .hidden-sm { display: none; }
          @media (min-width: 640px) { .hidden-sm { display: inline; } }
        `}</style>
        <SiteHeader />
        <main>{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}

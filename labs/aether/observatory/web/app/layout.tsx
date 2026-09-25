import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aether Observatory — CELESTRA X",
  description: "Cognitive architecture observatory for Aether Lab",
};

const NAV = [
  { href: "/cognition", label: "Cognition" },
  { href: "/attention", label: "Attention Map" },
  { href: "/tasks", label: "Task Graph" },
  { href: "/reflection", label: "Reflection" },
  { href: "/critique", label: "Critique" },
] as const;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-6 py-8">
          <header className="mb-10 border-b border-white/10 pb-6">
            <p className="font-mono text-xs uppercase tracking-[0.2em] text-aether-mute">
              CELESTRA X · Aether Lab
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-aether-ink">
              Aether Observatory
            </h1>
            <nav className="mt-6 flex flex-wrap gap-4 text-sm">
              {NAV.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="text-aether-mute transition hover:text-aether-accent"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </header>
          <main className="flex-1">{children}</main>
        </div>
      </body>
    </html>
  );
}

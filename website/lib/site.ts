/** Canonical public URLs for the AetherOS flagship site. */

export const site = {
  name: "AetherOS",
  org: "CELESTRA",
  tagline: "The Intelligence Infrastructure",
  description:
    "AetherOS is explainable operating intelligence — observe, reason, simulate, and recommend without mutating live infrastructure.",
  url: "https://aetheros-pied.vercel.app",

  /** Public GitHub — CELESTRA org repo. */
  github: {
    orgUrl: "https://github.com/Celestra-tech",
    repoUrl: "https://github.com/Celestra-tech/AetherOS",
    repoClone: "https://github.com/Celestra-tech/AetherOS.git",
    repoName: "AetherOS",
    owner: "Celestra-tech",
  },

  install: [
    "git clone https://github.com/Celestra-tech/AetherOS.git",
    "cd AetherOS",
    "python3.12 -m venv .venv && source .venv/bin/activate",
    'pip install -U pip && pip install -e ".[dev]"',
    "python -m aetheros          # Rich operator dashboard",
    "aetheros-horizon            # Horizon Observatory",
  ],
} as const;

export const navPrimary = [
  { href: "/problem", label: "Problem" },
  { href: "/architecture", label: "Architecture" },
  { href: "/resource-graph", label: "Resource Graph" },
  { href: "/digital-twin", label: "Digital Twin" },
  { href: "/global-knowledge-graph", label: "Knowledge Graph" },
] as const;

export const navSecondary = [
  { href: "/benchmarks", label: "Benchmarks" },
  { href: "/open-source", label: "Open Source" },
  { href: "/enterprise", label: "Enterprise" },
  { href: "/research", label: "Research" },
] as const;

export const footerProduct = [
  ...navPrimary,
  { href: "/planetary-scheduler", label: "Scheduler" },
  { href: "/horizon-observatory", label: "Observatory" },
] as const;

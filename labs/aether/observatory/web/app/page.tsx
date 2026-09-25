import Link from "next/link";

export default function HomePage() {
  return (
    <section className="space-y-6">
      <h2 className="text-2xl font-semibold">Cognitive Architecture</h2>
      <p className="max-w-2xl text-aether-mute">
        Aether performs cognition — attention, decomposition, planning,
        reflection, and critique. Foundation models perform inference.
        Module 1 ships the Attention Engine.
      </p>
      <Link
        href="/attention"
        className="inline-flex rounded-md bg-aether-accent px-4 py-2 text-sm font-medium text-aether-bg"
      >
        Open Attention Map
      </Link>
    </section>
  );
}

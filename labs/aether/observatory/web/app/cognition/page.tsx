export default function CognitionPage() {
  return (
    <section className="space-y-3">
      <h2 className="text-2xl font-semibold">Cognition</h2>
      <p className="text-aether-mute">
        Draft cognition plans are produced by Module 1 via{" "}
        <code className="font-mono text-aether-accent">POST /aether/cognition</code>.
        Full hierarchical planning ships in later modules.
      </p>
    </section>
  );
}

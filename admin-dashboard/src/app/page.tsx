export default function HomePage() {
  return (
    <main style={{ fontFamily: "sans-serif", padding: 32 }}>
      <h1>Prediqo Admin</h1>
      <p>Foundation placeholder. Full administration features arrive in Phase 9.</p>
      <p>
        API: <code>{process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}</code>
      </p>
    </main>
  );
}

import { useState } from "react";
import { Counter } from "./components/Counter";

// Tokens resolved from specs/design-system.yaml (primary + spacing.md).
const theme = {
  colors: { primary: "#1e40af", surface: "#ffffff" },
  spacing: { md: 16 },
};

export function App() {
  const [count, setCount] = useState(0);
  return (
    <main
      data-testid="app-root"
      style={{
        background: theme.colors.surface,
        padding: theme.spacing.md,
        color: theme.colors.primary,
      }}
    >
      <h1>Counter</h1>
      <Counter value={count} onInc={() => setCount((n) => n + 1)} onReset={() => setCount(0)} />
    </main>
  );
}

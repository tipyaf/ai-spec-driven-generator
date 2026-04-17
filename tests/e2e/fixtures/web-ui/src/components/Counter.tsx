type Props = {
  value: number;
  onInc: () => void;
  onReset: () => void;
};

const tokens = {
  primary: "#1e40af",
  surface: "#ffffff",
  gap: 8,
};

export function Counter({ value, onInc, onReset }: Props) {
  return (
    <section style={{ display: "flex", gap: tokens.gap, alignItems: "center" }}>
      <output data-testid="counter" style={{ color: tokens.primary }}>
        {value}
      </output>
      <button data-action="increment" onClick={onInc}>
        +1
      </button>
      <button data-action="reset" onClick={onReset}>
        reset
      </button>
    </section>
  );
}

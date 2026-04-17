// Vitest tests for the counter fixture. Not executed by pytest — consumed
// as-is by the fixture. We only check their shape in Python tests.
import { describe, it, expect } from "vitest";

describe("counter initial", () => {
  it("renders 0 at mount", () => {
    expect(0).toBe(0);
  });
});

describe("counter increment", () => {
  it("goes 0 -> 1 on click", () => {
    expect(0 + 1).toBe(1);
  });
});

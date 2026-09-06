import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Testing Library's automatic per-test cleanup only self-registers when it
// detects Vitest's globals; this project doesn't enable `test.globals`, so
// register it explicitly. Without this, DOM from earlier tests in the same
// file accumulates and can make later text/role queries match multiple
// elements.
afterEach(() => {
  cleanup();
});

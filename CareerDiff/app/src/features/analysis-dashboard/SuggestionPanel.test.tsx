import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SuggestionPanel } from "./SuggestionPanel";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("SuggestionPanel", () => {
  it("renders duplicate suggestions without duplicate React key errors", () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => undefined);
    const duplicate = "LLM 보완 프로젝트의 문제, 구현, 테스트, 결과를 한 문단으로 정리하세요.";

    render(
      <SuggestionPanel
        resumeSuggestions={{
          bullets: [],
          projectDescriptions: [duplicate, duplicate],
          skillPriority: [],
          atsKeywords: [],
        }}
      />,
    );

    expect(screen.getAllByText(duplicate)).toHaveLength(2);
    expect(consoleError).not.toHaveBeenCalledWith(
      expect.stringContaining("Encountered two children with the same key"),
    );
  });
});

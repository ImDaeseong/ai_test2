import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { mockAnalysisResult } from "@/core/mocks/mockAnalysisResult";
import { VALIDATION_CASES_STORAGE_KEY } from "@/core/validation/analysisValidationStore";
import AnalyzerPage from "./page";

/**
 * The main page restores its last result from localStorage on mount (cheap,
 * synchronous) but must never fetch the full accumulated history (data/*.json)
 * -- that list only grows and is checked occasionally via /history, not on
 * every analyzer page load. This guards both halves of that split.
 */
describe("AnalyzerPage mount", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("does not fetch the validation-case history on mount", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    window.localStorage.setItem(
      VALIDATION_CASES_STORAGE_KEY,
      JSON.stringify([
        {
          id: crypto.randomUUID(),
          createdAt: new Date().toISOString(),
          jobDescription: "job description",
          candidateProfile: "candidate profile",
          result: mockAnalysisResult,
        },
      ]),
    );

    render(<AnalyzerPage />);

    await waitFor(() => {
      expect(screen.getByText("적합도 점수")).toBeInTheDocument();
    });
    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });

  it("restores the last locally stored result on mount, but not a growing history list", async () => {
    window.localStorage.setItem(
      VALIDATION_CASES_STORAGE_KEY,
      JSON.stringify([
        {
          id: crypto.randomUUID(),
          createdAt: new Date().toISOString(),
          jobDescription: "job description",
          candidateProfile: "candidate profile",
          result: mockAnalysisResult,
        },
      ]),
    );

    render(<AnalyzerPage />);

    await waitFor(() => {
      expect(screen.getByText("적합도 점수")).toBeInTheDocument();
    });
    expect(screen.queryByText(/분석 히스토리 \(/)).not.toBeInTheDocument();
  });

  it("shows nothing below the form when no case has been stored yet", () => {
    render(<AnalyzerPage />);
    expect(screen.queryByText("적합도 점수")).not.toBeInTheDocument();
  });

  it("links to the /history page for browsing past analyses", () => {
    render(<AnalyzerPage />);
    expect(screen.getByRole("link", { name: "분석 히스토리 보기" })).toHaveAttribute("href", "/history");
  });
});

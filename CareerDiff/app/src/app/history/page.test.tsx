import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mockAnalysisResult } from "@/core/mocks/mockAnalysisResult";
import type { CareerDiffAnalysisResult } from "@/core/types";
import { VALIDATION_CASES_STORAGE_KEY } from "@/core/validation/analysisValidationStore";
import ValidationHistoryPage from "./page";

/**
 * Exercises the full handoff this bug crossed: localStorage/server ->
 * loadValidationCases -> mount effect -> AnalysisDashboard ->
 * RelatedSkillPanel. A unit test on loadValidationCases alone can't catch a
 * broken handoff between those modules; this renders the real page
 * component against seeded storage/fetch.
 */
describe("ValidationHistoryPage", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("does not crash and recovers a stored case that predates relatedSkillGuidance", async () => {
    const staleResult: Record<string, unknown> = { ...mockAnalysisResult };
    delete staleResult.relatedSkillGuidance;
    window.localStorage.setItem(
      VALIDATION_CASES_STORAGE_KEY,
      JSON.stringify([
        {
          id: crypto.randomUUID(),
          createdAt: new Date().toISOString(),
          jobDescription: "job description",
          candidateProfile: "candidate profile",
          result: staleResult,
        },
      ]),
    );

    render(<ValidationHistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("적합도 점수")).toBeInTheDocument();
    });
    expect(screen.getByText("연결된 기술 정보가 없습니다.")).toBeInTheDocument();
  });

  it("shows an empty-state message when the only stored case is malformed beyond recovery", async () => {
    window.localStorage.setItem(
      VALIDATION_CASES_STORAGE_KEY,
      JSON.stringify([
        {
          id: crypto.randomUUID(),
          createdAt: new Date().toISOString(),
          jobDescription: "job description",
          candidateProfile: "candidate profile",
          result: { fitScore: mockAnalysisResult.fitScore },
        },
      ]),
    );

    render(<ValidationHistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("아직 누적된 분석 결과가 없습니다.")).toBeInTheDocument();
    });
    expect(screen.queryByText("적합도 점수")).not.toBeInTheDocument();
  });

  it("renders the dashboard, including the related-skill panel, for a valid stored case", async () => {
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

    render(<ValidationHistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("적합도 점수")).toBeInTheDocument();
    });
    expect(screen.getByText("연관 기술 가이드")).toBeInTheDocument();
  });

  it("switches the displayed result when a different history entry is selected", async () => {
    const secondResult: CareerDiffAnalysisResult = {
      ...mockAnalysisResult,
      summary: "두 번째 케이스 전용 요약 텍스트입니다.",
      fitScore: { ...mockAnalysisResult.fitScore, total: 12 },
    };
    window.localStorage.setItem(
      VALIDATION_CASES_STORAGE_KEY,
      JSON.stringify([
        {
          id: "case-first",
          createdAt: "2026-08-01T00:00:00.000Z",
          jobDescription: "첫 번째 채용공고 원문입니다.",
          candidateProfile: "candidate profile one",
          result: mockAnalysisResult,
        },
        {
          id: "case-second",
          createdAt: "2026-08-02T00:00:00.000Z",
          jobDescription: "두 번째 채용공고 원문입니다.",
          candidateProfile: "candidate profile two",
          result: secondResult,
        },
      ]),
    );

    render(<ValidationHistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("분석 히스토리 (2건)")).toBeInTheDocument();
    });
    // The mount effect auto-selects the most recent case (secondResult).
    await waitFor(() => {
      expect(screen.getByText(secondResult.summary)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/첫 번째 채용공고/));

    await waitFor(() => {
      expect(screen.getByText(mockAnalysisResult.summary)).toBeInTheDocument();
    });
  });

  it("shows a case saved on the server even when this browser's localStorage is empty", async () => {
    const serverOnlyResult: CareerDiffAnalysisResult = {
      ...mockAnalysisResult,
      summary: "다른 브라우저에서 저장된 서버 케이스 요약입니다.",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          cases: [
            {
              id: "server-case",
              createdAt: "2026-08-03T00:00:00.000Z",
              jobDescription: "server-persisted job description",
              candidateProfile: "server-persisted candidate profile",
              result: serverOnlyResult,
            },
          ],
        }),
      }),
    );

    render(<ValidationHistoryPage />);

    await waitFor(() => {
      expect(screen.getByText(serverOnlyResult.summary)).toBeInTheDocument();
    });
    expect(screen.getByText("분석 히스토리 (1건)")).toBeInTheDocument();
  });

  it("links back to the analyzer page", async () => {
    render(<ValidationHistoryPage />);
    await waitFor(() => {
      expect(screen.getByRole("link", { name: "분석하기로 돌아가기" })).toHaveAttribute("href", "/");
    });
  });
});

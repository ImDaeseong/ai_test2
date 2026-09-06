import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { mockAnalysisResult } from "@/core/mocks/mockAnalysisResult";
import type { AnalysisValidationCase } from "@/core/validation/analysisValidationStore";
import { ValidationCaseHistoryPanel } from "./ValidationCaseHistoryPanel";

function makeCase(overrides: Partial<AnalysisValidationCase> = {}): AnalysisValidationCase {
  return {
    id: "case-1",
    createdAt: "2026-08-01T00:00:00.000Z",
    jobDescription: "백엔드 개발자를 채용합니다.",
    candidateProfile: "Python 경험이 있습니다.",
    result: mockAnalysisResult,
    ...overrides,
  };
}

describe("ValidationCaseHistoryPanel", () => {
  it("renders nothing when there are no cases", () => {
    const { container } = render(
      <ValidationCaseHistoryPanel cases={[]} selectedCaseId={null} onSelect={() => {}} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("lists each case with its fit score and related-skill-guidance count", () => {
    render(
      <ValidationCaseHistoryPanel
        cases={[makeCase()]}
        selectedCaseId={null}
        onSelect={() => {}}
      />,
    );

    expect(screen.getByText("분석 히스토리 (1건)")).toBeInTheDocument();
    expect(screen.getByText(`적합도 ${mockAnalysisResult.fitScore.total}점`)).toBeInTheDocument();
    expect(
      screen.getByText(`연관 기술 가이드 ${mockAnalysisResult.relatedSkillGuidance.length}건`),
    ).toBeInTheDocument();
  });

  it("calls onSelect with the clicked case", () => {
    const onSelect = vi.fn();
    const target = makeCase({ id: "case-2" });
    render(
      <ValidationCaseHistoryPanel cases={[makeCase({ id: "case-1" }), target]} selectedCaseId={null} onSelect={onSelect} />,
    );

    fireEvent.click(screen.getAllByRole("button")[0]);
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect.mock.calls[0][0].id).toBe(target.id);
  });

  it("marks the selected case as pressed", () => {
    render(
      <ValidationCaseHistoryPanel cases={[makeCase({ id: "case-1" })]} selectedCaseId="case-1" onSelect={() => {}} />,
    );
    expect(screen.getByRole("button", { pressed: true })).toBeInTheDocument();
  });
});

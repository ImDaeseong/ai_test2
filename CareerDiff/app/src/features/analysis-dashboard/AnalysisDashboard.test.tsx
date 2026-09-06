import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { mockAnalysisResult } from "@/core/mocks/mockAnalysisResult";
import type { CareerDiffAnalysisResult } from "@/core/types";
import { AnalysisDashboard } from "./AnalysisDashboard";

describe("AnalysisDashboard", () => {
  it("renders all MVP sections for the mock result (docs/PRODUCT.md)", () => {
    render(<AnalysisDashboard result={mockAnalysisResult} />);

    expect(screen.getByText("적합도 점수")).toBeInTheDocument();
    expect(screen.getByText("채용 요건")).toBeInTheDocument();
    expect(screen.getByText("매칭 결과")).toBeInTheDocument();
    expect(screen.getByText("이력서 개선 제안")).toBeInTheDocument();
    expect(screen.getByText("보완 프로젝트 추천")).toBeInTheDocument();
    expect(screen.getByText("연관 기술 가이드")).toBeInTheDocument();
    expect(screen.getByText("면접 준비")).toBeInTheDocument();
  });

  it("shows no no-match notice when strong matches exist", () => {
    render(<AnalysisDashboard result={mockAnalysisResult} />);
    expect(screen.queryByText(/직접 일치하는 이력서 근거가 없습니다/)).not.toBeInTheDocument();
    expect(screen.queryByText(/비교할 기술 요건을 추출하지 못했습니다/)).not.toBeInTheDocument();
  });

  it("explains a mismatch when there are requirements but no strong match", () => {
    const mismatch: CareerDiffAnalysisResult = {
      ...mockAnalysisResult,
      matches: { strong: [], weak: [], missing: [], risks: [] },
    };
    render(<AnalysisDashboard result={mismatch} />);
    expect(screen.getByText(/직접 일치하는 이력서 근거가 없습니다/)).toBeInTheDocument();
  });

  it("points at the empty job when no requirements were extracted", () => {
    const emptyJob: CareerDiffAnalysisResult = {
      ...mockAnalysisResult,
      jobRequirements: { ...mockAnalysisResult.jobRequirements, requiredSkills: [], preferredSkills: [] },
      matches: { strong: [], weak: [], missing: [], risks: [] },
    };
    render(<AnalysisDashboard result={emptyJob} />);
    expect(screen.getByText(/비교할 기술 요건을 추출하지 못했습니다/)).toBeInTheDocument();
  });

  it("does not break layout when result sections are empty", () => {
    const emptyResult: CareerDiffAnalysisResult = {
      ...mockAnalysisResult,
      fitScore: { total: 0, categories: [] },
      jobRequirements: {
        requiredSkills: [],
        preferredSkills: [],
        domain: [],
        collaboration: [],
        deliveryExpectations: [],
      },
      matches: { strong: [], weak: [], missing: [], risks: [] },
      resumeSuggestions: { bullets: [], projectDescriptions: [], skillPriority: [], atsKeywords: [] },
      miniProjects: [],
      relatedSkillGuidance: [],
      interviewPrep: { questions: [], weakAreas: [], sevenDayPlan: [] },
    };

    render(<AnalysisDashboard result={emptyResult} />);

    expect(screen.getAllByText(/없습니다\.?$/).length).toBeGreaterThan(0);
  });
});

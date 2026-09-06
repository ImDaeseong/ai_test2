import { describe, expect, it } from "vitest";
import { mockAnalysisResult } from "./mockAnalysisResult";

describe("mockAnalysisResult", () => {
  it("follows the MVP retrieval defaults from ANALYSIS_FLOW.md", () => {
    expect(mockAnalysisResult.retrievalContext.enabled).toBe(false);
    expect(mockAnalysisResult.retrievalContext.provider).toBe("none");
    expect(mockAnalysisResult.metadata.retrievalUsed).toBe(false);
    expect(mockAnalysisResult.metadata.persisted).toBe(false);
  });

  it("has a fit score in range and at least one category", () => {
    expect(mockAnalysisResult.fitScore.total).toBeGreaterThanOrEqual(0);
    expect(mockAnalysisResult.fitScore.total).toBeLessThanOrEqual(100);
    expect(mockAnalysisResult.fitScore.categories.length).toBeGreaterThan(0);
  });

  it("covers all four match statuses so dashboard panels have something to render", () => {
    expect(mockAnalysisResult.matches.strong.length).toBeGreaterThan(0);
    expect(mockAnalysisResult.matches.weak.length).toBeGreaterThan(0);
    expect(mockAnalysisResult.matches.missing.length).toBeGreaterThan(0);
    expect(mockAnalysisResult.matches.risks.length).toBeGreaterThan(0);
  });

  it("provides at least one resume bullet and interview question", () => {
    expect(mockAnalysisResult.resumeSuggestions.bullets.length).toBeGreaterThan(0);
    expect(mockAnalysisResult.interviewPrep.questions.length).toBeGreaterThan(0);
  });

  it("recommends exactly 3 mini projects, each mapped to a target gap (docs/PRODUCT.md)", () => {
    expect(mockAnalysisResult.miniProjects).toHaveLength(3);
    for (const project of mockAnalysisResult.miniProjects) {
      expect(project.targetGaps.length).toBeGreaterThan(0);
    }
  });
});

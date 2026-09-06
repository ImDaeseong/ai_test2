import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { mockAnalysisResult } from "@/core/mocks/mockAnalysisResult";
import { AnalysisJsonPanel } from "./AnalysisJsonPanel";

describe("AnalysisJsonPanel", () => {
  it("shows the JSON result and accumulated validation count", () => {
    render(<AnalysisJsonPanel result={mockAnalysisResult} validationCount={3} />);

    expect(screen.getByText(/검증 데이터 3건이 누적되어 있습니다/)).toBeInTheDocument();
    expect(screen.getByText(/누적되어도 분석\s*품질이 올라가지는 않습니다/)).toBeInTheDocument();
    expect(screen.getByText("현재 결과 JSON 다운로드")).toBeInTheDocument();
    expect(screen.getByText("누적 검증 데이터 다운로드")).toBeInTheDocument();
    expect(screen.getByText(/"fitScore"/)).toBeInTheDocument();
  });
});

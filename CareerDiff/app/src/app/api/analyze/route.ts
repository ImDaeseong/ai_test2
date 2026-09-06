import { NextResponse } from "next/server";
import {
  AnalysisOrchestrator,
  AnalysisOrchestratorValidationError,
  AnalysisProviderError,
} from "@/core/analysis/AnalysisOrchestrator";
import type { AnalyzeResponse, ApiErrorResponse } from "@/core/types";

// Per docs/ARCHITECTURE.md: only this route calls AnalysisOrchestrator.
const orchestrator = new AnalysisOrchestrator();

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    // Do not log the raw body (docs/ARCHITECTURE.md privacy requirements).
    return NextResponse.json<ApiErrorResponse>(
      { error: { code: "VALIDATION_ERROR", message: "Request body must be valid JSON.", retryable: false } },
      { status: 400 },
    );
  }

  try {
    const result = await orchestrator.analyze(body);
    const response: AnalyzeResponse = {
      result,
      privacy: {
        persisted: false,
        rawInputLogged: false,
        retrievalUsed: result.metadata.retrievalUsed,
      },
    };
    return NextResponse.json(response);
  } catch (error) {
    if (error instanceof AnalysisOrchestratorValidationError) {
      return NextResponse.json<ApiErrorResponse>(
        { error: { code: "VALIDATION_ERROR", message: error.issues.join(" "), retryable: false } },
        { status: 400 },
      );
    }
    if (error instanceof AnalysisProviderError) {
      // Do not log error.message here — it may echo provider-side details derived from raw input.
      return NextResponse.json<ApiErrorResponse>(
        { error: { code: "ANALYSIS_FAILED", message: "AI 분석에 실패했습니다. 잠시 후 다시 시도해 주세요.", retryable: true } },
        { status: 502 },
      );
    }
    return NextResponse.json<ApiErrorResponse>(
      { error: { code: "ANALYSIS_FAILED", message: "Analysis failed unexpectedly.", retryable: true } },
      { status: 500 },
    );
  }
}

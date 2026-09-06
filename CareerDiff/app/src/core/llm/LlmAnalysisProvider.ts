import type { AnalyzeRequestInput } from "@/core/schemas/analyzeRequest";
import type { CareerDiffAnalysisResult } from "@/core/types";

/**
 * Boundary between AnalysisOrchestrator and any real analysis backend.
 * Lets the orchestrator branch on configuration state and lets tests
 * inject a fake implementation instead of calling a real provider.
 */
export interface LlmAnalysisProvider {
  /** Whether this provider has what it needs (e.g. an API key) to run. */
  isConfigured(): boolean;
  /** Throws on failure; must not silently return mock/fabricated data. */
  generate(input: AnalyzeRequestInput): Promise<CareerDiffAnalysisResult>;
}

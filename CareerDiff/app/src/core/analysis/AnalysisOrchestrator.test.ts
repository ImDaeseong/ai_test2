import { describe, expect, it } from "vitest";
import type { LlmAnalysisProvider } from "@/core/llm/LlmAnalysisProvider";
import { mockAnalysisResult } from "@/core/mocks/mockAnalysisResult";
import { careerDiffAnalysisResultSchema } from "@/core/schemas/analysisResult";
import { AnalysisOrchestrator, AnalysisOrchestratorValidationError, AnalysisProviderError } from "./AnalysisOrchestrator";

const validRequest = {
  jobDescription: "a".repeat(40),
  candidateProfile: "b".repeat(40),
};

/** Never makes a real network call — a test double for LlmAnalysisProvider. */
class FakeLlmProvider implements LlmAnalysisProvider {
  constructor(
    private readonly configured: boolean,
    private readonly result: () => Promise<import("@/core/types").CareerDiffAnalysisResult>,
  ) {}

  isConfigured(): boolean {
    return this.configured;
  }

  generate(): Promise<import("@/core/types").CareerDiffAnalysisResult> {
    return this.result();
  }
}

describe("AnalysisOrchestrator (default provider, no API key in this environment)", () => {
  const orchestrator = new AnalysisOrchestrator();

  it("rejects a request with an empty job description", async () => {
    await expect(orchestrator.analyze({ jobDescription: "", candidateProfile: "b".repeat(40) })).rejects.toThrow(
      AnalysisOrchestratorValidationError,
    );
  });

  it("rejects a request with a too-short candidate profile", async () => {
    await expect(orchestrator.analyze({ jobDescription: "a".repeat(40), candidateProfile: "short" })).rejects.toThrow(
      AnalysisOrchestratorValidationError,
    );
  });

  it("rejects a non-object request body", async () => {
    await expect(orchestrator.analyze(null)).rejects.toThrow(AnalysisOrchestratorValidationError);
    await expect(orchestrator.analyze("not json")).rejects.toThrow(AnalysisOrchestratorValidationError);
  });

  it("returns an input-dependent local result when no LLM provider is configured", async () => {
    const result = await orchestrator.analyze(validRequest);
    expect(result.metadata.modelVersion).toBe("local-keyword-analyzer");
  });

  it("returns MVP retrieval defaults regardless of input", async () => {
    const result = await orchestrator.analyze(validRequest);
    expect(result.retrievalContext.enabled).toBe(false);
    expect(result.retrievalContext.provider).toBe("none");
  });
});

describe("AnalysisOrchestrator (dependency-injected fake provider, no real API calls)", () => {
  it("uses local analysis when an injected provider is not configured", async () => {
    const provider = new FakeLlmProvider(false, async () => {
      throw new Error("generate() must not be called when the provider reports unconfigured.");
    });
    const orchestrator = new AnalysisOrchestrator(provider);
    const result = await orchestrator.analyze(validRequest);
    expect(result.metadata.modelVersion).toBe("local-keyword-analyzer");
  });

  it("uses the provider's result when isConfigured() is true", async () => {
    const providerResult = { ...mockAnalysisResult, summary: "provider-backed result" };
    const provider = new FakeLlmProvider(true, async () => providerResult);
    const orchestrator = new AnalysisOrchestrator(provider);
    const result = await orchestrator.analyze(validRequest);
    expect(result.summary).toBe("provider-backed result");
  });

  it("wraps a configured provider's failure as AnalysisProviderError instead of falling back to mock", async () => {
    const provider = new FakeLlmProvider(true, async () => {
      throw new Error("upstream timeout");
    });
    const orchestrator = new AnalysisOrchestrator(provider);
    await expect(orchestrator.analyze(validRequest)).rejects.toThrow(AnalysisProviderError);
  });
});

describe("mockAnalysisResult vs careerDiffAnalysisResultSchema", () => {
  it("validates against the same schema used to build the LLM structured-output request", () => {
    expect(() => careerDiffAnalysisResultSchema.parse(mockAnalysisResult)).not.toThrow();
  });
});

import type { LlmAnalysisProvider } from "@/core/llm/LlmAnalysisProvider";
import { OpenAiAnalysisProvider } from "@/core/llm/OpenAiAnalysisProvider";
import { buildLocalAnalysis } from "@/core/analysis/LocalAnalysisProvider";
import { analyzeRequestSchema } from "@/core/schemas/analyzeRequest";
import type { CareerDiffAnalysisResult } from "@/core/types";

export class AnalysisOrchestratorValidationError extends Error {
  readonly issues: string[];

  constructor(issues: string[]) {
    super("Invalid analyze request.");
    this.name = "AnalysisOrchestratorValidationError";
    this.issues = issues;
  }
}

/** A configured LLM provider failed while generating an analysis. */
export class AnalysisProviderError extends Error {
  readonly failureKind: "timeout" | "rate_limit" | "auth" | "provider" | "unexpected";

  constructor(failureKind: AnalysisProviderError["failureKind"]) {
    super("OpenAI analysis failed.");
    this.name = "AnalysisProviderError";
    this.failureKind = failureKind;
  }
}

function classifyProviderFailure(error: unknown): AnalysisProviderError["failureKind"] {
  const candidate = error as { name?: unknown; status?: unknown; code?: unknown };
  const name = typeof candidate?.name === "string" ? candidate.name.toLowerCase() : "";
  const code = typeof candidate?.code === "string" ? candidate.code.toLowerCase() : "";
  const status = typeof candidate?.status === "number" ? candidate.status : 0;
  if (name.includes("timeout") || code.includes("timeout")) return "timeout";
  if (status === 429 || name.includes("ratelimit") || code.includes("rate_limit")) return "rate_limit";
  if (status === 401 || status === 403 || name.includes("authentication")) return "auth";
  if (status >= 500) return "provider";
  return "unexpected";
}

/** A configured external provider was requested without explicit user consent. */
export class ExternalProcessingConsentError extends Error {
  constructor() {
    super("External processing consent is required.");
    this.name = "ExternalProcessingConsentError";
  }
}

/**
 * Coordinates one job-fit analysis request.
 *
 * Per docs/ARCHITECTURE.md, this is the only module allowed to
 * call extraction/matching/scoring/generation services and the only module
 * allowed to request RetrievalContext. Only the API route should call this
 * class; it must not be imported directly by UI components.
 *
 * Local-first with an optional LLM key (docs/ARCHITECTURE.md):
 * - No API key configured (the default — nothing in this repo sets one):
 *   analyzes the actual inputs with the deterministic local analyzer.
 * - API key configured (OPENAI_API_KEY, see .env.example): calls the real
 *   provider. A failure there is a real error, not silently masked by
 *   falling back to mock data — see AnalysisProviderError.
 *
 * The provider is injected (defaulting to OpenAiAnalysisProvider) so
 * tests can exercise both branches without ever making a real API call.
 */
export class AnalysisOrchestrator {
  constructor(private readonly llmProvider: LlmAnalysisProvider = new OpenAiAnalysisProvider()) {}

  async analyze(rawInput: unknown): Promise<CareerDiffAnalysisResult> {
    const parsed = analyzeRequestSchema.safeParse(rawInput);
    if (!parsed.success) {
      throw new AnalysisOrchestratorValidationError(parsed.error.issues.map((issue) => issue.message));
    }

    if (!this.llmProvider.isConfigured()) {
      return buildLocalAnalysis(parsed.data);
    }

    if (!parsed.data.allowExternalProcessing) {
      throw new ExternalProcessingConsentError();
    }

    try {
      return await this.llmProvider.generate(parsed.data);
    } catch (error) {
      throw new AnalysisProviderError(classifyProviderFailure(error));
    }
  }
}

import OpenAI from "openai";
import { z } from "zod";
import type { AnalyzeRequestInput } from "@/core/schemas/analyzeRequest";
import { careerDiffAnalysisResultSchema } from "@/core/schemas/analysisResult";
import type { CareerDiffAnalysisResult } from "@/core/types";
import { buildAnalysisPrompt } from "./buildAnalysisPrompt";
import type { LlmAnalysisProvider } from "./LlmAnalysisProvider";

const DEFAULT_MODEL = "gpt-4o-mini";

type JsonSchema = Record<string, unknown>;

/**
 * OpenAI strict structured outputs require every object property to appear in
 * `required`. Domain-level optional fields are represented as required,
 * nullable properties for the provider, then normalized back to absent fields
 * before the regular Zod result schema validates the response.
 */
export function toOpenAiStrictSchema(schema: JsonSchema): JsonSchema {
  const result = structuredClone(schema);

  function visit(node: unknown) {
    if (Array.isArray(node)) {
      node.forEach(visit);
      return;
    }
    if (!node || typeof node !== "object") return;

    const objectNode = node as JsonSchema;
    const properties = objectNode.properties;
    if (properties && typeof properties === "object" && !Array.isArray(properties)) {
      const propertyMap = properties as Record<string, unknown>;
      const previouslyRequired = new Set(Array.isArray(objectNode.required) ? objectNode.required : []);

      for (const [key, propertySchema] of Object.entries(propertyMap)) {
        visit(propertySchema);
        if (!previouslyRequired.has(key)) {
          propertyMap[key] = { anyOf: [propertySchema, { type: "null" }] };
        }
      }
      objectNode.required = Object.keys(propertyMap);
    }

    for (const [key, value] of Object.entries(objectNode)) {
      if (key !== "properties") visit(value);
    }
  }

  visit(result);
  return result;
}

export function omitNullObjectFields(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(omitNullObjectFields);
  if (!value || typeof value !== "object") return value;

  return Object.fromEntries(
    Object.entries(value)
      .filter(([, child]) => child !== null)
      .map(([key, child]) => [key, omitNullObjectFields(child)]),
  );
}

/**
 * OpenAI Responses API + Structured Outputs
 * (docs/ARCHITECTURE.md).
 *
 * Reads the key from OPENAI_API_KEY (see .env.example, left blank on
 * purpose). isConfigured() gates every call — AnalysisOrchestrator only
 * reaches generate() when a key is present, and otherwise falls back to the
 * deterministic local analyzer (LocalAnalysisProvider), not a mock.
 *
 * Not yet exercised against the real API in this repo (no OPENAI_API_KEY is
 * configured here), but generate()'s full pipeline — strict-schema request,
 * response parse, null stripping, and Zod validation — is covered by a
 * mocked-client unit test, along with provider selection and the
 * required+nullable strict-schema conversion. Before production, run one
 * consented, synthetic request with a real key and confirm the response
 * validates against careerDiffAnalysisResultSchema.
 */
export class OpenAiAnalysisProvider implements LlmAnalysisProvider {
  isConfigured(): boolean {
    return Boolean(process.env.OPENAI_API_KEY);
  }

  async generate(input: AnalyzeRequestInput): Promise<CareerDiffAnalysisResult> {
    if (!this.isConfigured()) {
      throw new Error("OPENAI_API_KEY is not set.");
    }

    const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
    const model = process.env.OPENAI_MODEL || DEFAULT_MODEL;
    const jsonSchema = toOpenAiStrictSchema(z.toJSONSchema(careerDiffAnalysisResultSchema));

    const response = await client.responses.create({
      model,
      input: buildAnalysisPrompt(input),
      text: {
        format: {
          type: "json_schema",
          name: "career_diff_analysis_result",
          schema: jsonSchema,
          strict: true,
        },
      },
    });

    const raw: unknown = omitNullObjectFields(JSON.parse(response.output_text));
    return careerDiffAnalysisResultSchema.parse(raw);
  }
}

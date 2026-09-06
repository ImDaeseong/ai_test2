import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { z } from "zod";
import { mockAnalysisResult } from "@/core/mocks/mockAnalysisResult";
import { careerDiffAnalysisResultSchema } from "@/core/schemas/analysisResult";
import { OpenAiAnalysisProvider, omitNullObjectFields, toOpenAiStrictSchema } from "./OpenAiAnalysisProvider";

// Mock the OpenAI SDK so generate() runs its full parse/normalize/validate
// pipeline without a real key or any network call (no cost).
const { responsesCreate } = vi.hoisted(() => ({ responsesCreate: vi.fn() }));
vi.mock("openai", () => ({
  default: class {
    responses = { create: responsesCreate };
  },
}));

function expectAllObjectPropertiesRequired(node: unknown) {
  if (Array.isArray(node)) {
    node.forEach(expectAllObjectPropertiesRequired);
    return;
  }
  if (!node || typeof node !== "object") return;

  const objectNode = node as Record<string, unknown>;
  const properties = objectNode.properties;
  if (properties && typeof properties === "object" && !Array.isArray(properties)) {
    expect(objectNode.required).toEqual(Object.keys(properties));
  }
  Object.values(objectNode).forEach(expectAllObjectPropertiesRequired);
}

describe("OpenAI structured-output schema", () => {
  it("marks every object property required for strict mode", () => {
    const schema = toOpenAiStrictSchema(z.toJSONSchema(careerDiffAnalysisResultSchema));

    expectAllObjectPropertiesRequired(schema);
  });

  it("makes domain-optional fields nullable and removes returned nulls before validation", () => {
    const schema = toOpenAiStrictSchema(z.toJSONSchema(careerDiffAnalysisResultSchema));
    const senioritySchema = (
      (schema.properties as Record<string, Record<string, unknown>>).jobRequirements.properties as Record<
        string,
        unknown
      >
    ).seniority;

    expect(senioritySchema).toEqual({ anyOf: [{ type: "string" }, { type: "null" }] });
    expect(
      omitNullObjectFields({
        seniority: null,
        nested: { evidenceSnippet: null, label: "TypeScript" },
        values: [{ sourceRecordId: null, id: "req-1" }],
      }),
    ).toEqual({
      nested: { label: "TypeScript" },
      values: [{ id: "req-1" }],
    });
  });
});

describe("OpenAiAnalysisProvider.generate", () => {
  beforeEach(() => {
    process.env.OPENAI_API_KEY = "test-key-not-real";
    responsesCreate.mockReset();
  });
  afterEach(() => {
    delete process.env.OPENAI_API_KEY;
  });

  it("parses a structured response, strips returned nulls, and validates the schema", async () => {
    // The LLM returns null for domain-optional fields (strict schema makes them
    // required+nullable); generate() must strip those before Zod validation.
    const payload = {
      ...mockAnalysisResult,
      jobRequirements: { ...mockAnalysisResult.jobRequirements, seniority: null },
    };
    responsesCreate.mockResolvedValue({ output_text: JSON.stringify(payload) });

    const result = await new OpenAiAnalysisProvider().generate({
      jobDescription: "채용공고 본문입니다. ".repeat(4),
      candidateProfile: "후보자 이력서입니다. ".repeat(4),
    });

    expect(responsesCreate).toHaveBeenCalledOnce();
    expect(result.fitScore.total).toBe(mockAnalysisResult.fitScore.total);
    expect(result.miniProjects).toHaveLength(mockAnalysisResult.miniProjects.length);
    expect("seniority" in result.jobRequirements).toBe(false);
    // Sanity: the returned object still satisfies the domain schema.
    expect(() => careerDiffAnalysisResultSchema.parse(result)).not.toThrow();
  });

  it("sends the model and the built prompt to the API", async () => {
    responsesCreate.mockResolvedValue({ output_text: JSON.stringify(mockAnalysisResult) });

    await new OpenAiAnalysisProvider().generate({
      jobDescription: "Python 백엔드 개발자를 찾습니다. ".repeat(2),
      candidateProfile: "Python 경력 3년입니다. ".repeat(2),
    });

    const args = responsesCreate.mock.calls[0][0];
    expect(args.model).toBe("gpt-4o-mini");
    expect(args.input).toContain("Python 백엔드 개발자");
    expect(args.text.format.type).toBe("json_schema");
    expect(args.text.format.strict).toBe(true);
  });

  it("throws when no API key is configured", async () => {
    delete process.env.OPENAI_API_KEY;
    await expect(
      new OpenAiAnalysisProvider().generate({ jobDescription: "x".repeat(40), candidateProfile: "y".repeat(40) }),
    ).rejects.toThrow(/OPENAI_API_KEY/);
    expect(responsesCreate).not.toHaveBeenCalled();
  });
});

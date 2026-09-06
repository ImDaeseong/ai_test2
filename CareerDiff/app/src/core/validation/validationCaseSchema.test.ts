import { describe, expect, it } from "vitest";
import { mockAnalysisResult } from "@/core/mocks/mockAnalysisResult";
import { analysisValidationCaseSchema } from "./validationCaseSchema";

describe("analysisValidationCaseSchema", () => {
  const validCase = {
    id: "b6fbf649-bfe7-4f85-9788-9716f41625db",
    createdAt: "2026-08-01T00:00:00.000Z",
    jobDescription: "job ".repeat(10),
    candidateProfile: "candidate ".repeat(10),
    result: mockAnalysisResult,
  };

  it("accepts a complete validation input-output pair", () => {
    expect(analysisValidationCaseSchema.safeParse(validCase).success).toBe(true);
  });

  it("rejects unsafe filenames and incomplete inputs through the id and text fields", () => {
    expect(analysisValidationCaseSchema.safeParse({ ...validCase, id: "../../escape" }).success).toBe(false);
    expect(analysisValidationCaseSchema.safeParse({ ...validCase, jobDescription: "short" }).success).toBe(false);
  });
});

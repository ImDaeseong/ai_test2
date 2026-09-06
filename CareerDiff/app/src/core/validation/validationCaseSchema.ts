import { z } from "zod";
import { careerDiffAnalysisResultSchema } from "@/core/schemas/analysisResult";

export const analysisValidationCaseSchema = z.object({
  id: z.string().uuid(),
  createdAt: z.string().datetime(),
  jobDescription: z.string().min(30).max(100_000),
  candidateProfile: z.string().min(30).max(100_000),
  result: careerDiffAnalysisResultSchema,
});

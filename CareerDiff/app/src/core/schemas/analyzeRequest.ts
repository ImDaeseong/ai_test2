import { z } from "zod";

/**
 * Validates POST /api/analyze request bodies.
 * Source of truth for the shape: docs/ARCHITECTURE.md.
 */

const MIN_TEXT_LENGTH = 30;
const MAX_TEXT_LENGTH = 20000;

const longText = z
  .string()
  .trim()
  .min(MIN_TEXT_LENGTH, `Please paste at least ${MIN_TEXT_LENGTH} characters.`)
  .max(MAX_TEXT_LENGTH, `Please paste at most ${MAX_TEXT_LENGTH} characters.`);

export const analyzeRequestSchema = z.object({
  jobDescription: longText,
  candidateProfile: longText,
  targetRole: z.string().trim().max(200).optional(),
  targetSeniority: z.string().trim().max(200).optional(),
  retrieval: z
    .object({
      enabled: z.boolean(),
      includeSavedEvidence: z.boolean().optional(),
      includePublicTaxonomy: z.boolean().optional(),
      includeHistoricalAnalyses: z.boolean().optional(),
    })
    .optional(),
});

export type AnalyzeRequestInput = z.infer<typeof analyzeRequestSchema>;

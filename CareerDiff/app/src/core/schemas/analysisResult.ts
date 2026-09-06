import { z } from "zod";

/**
 * Runtime schema for CareerDiffAnalysisResult, used to (1) validate
 * whatever JSON an LLM provider returns before it reaches the UI, and
 * (2) generate the structured-output JSON schema for the OpenAI request.
 * Source of truth for the shape: docs/ARCHITECTURE.md.
 */

const confidenceSchema = z.enum(["high", "medium", "low"]);
const visibilitySchema = z.enum(["private", "team", "public_taxonomy", "anonymized_aggregate"]);
const piiRiskSchema = z.enum(["low", "medium", "high"]);
const sourceTypeSchema = z.enum([
  "job_requirement",
  "candidate_evidence",
  "project_evidence",
  "skill_taxonomy",
  "analysis_summary",
]);

const requirementItemSchema = z.object({
  id: z.string(),
  label: z.string(),
  category: z.string(),
  evidenceSnippet: z.string().optional(),
  confidence: confidenceSchema,
  sourceRecordId: z.string().optional(),
});

const jobRequirementsSchema = z.object({
  requiredSkills: z.array(requirementItemSchema),
  preferredSkills: z.array(requirementItemSchema),
  domain: z.array(requirementItemSchema),
  seniority: z.string().optional(),
  collaboration: z.array(requirementItemSchema),
  deliveryExpectations: z.array(requirementItemSchema),
});

const evidenceItemSchema = z.object({
  id: z.string(),
  label: z.string(),
  sourceSnippet: z.string(),
  confidence: confidenceSchema,
  sourceRecordId: z.string().optional(),
});

const candidateEvidenceSchema = z.object({
  skills: z.array(evidenceItemSchema),
  projects: z.array(evidenceItemSchema),
  responsibilities: z.array(evidenceItemSchema),
  achievements: z.array(evidenceItemSchema),
  collaboration: z.array(evidenceItemSchema),
});

const matchItemSchema = z.object({
  requirement: z.string(),
  status: z.enum(["strong", "weak", "missing", "risk"]),
  reason: z.string(),
  evidenceSnippet: z.string().optional(),
  sourceRequirementId: z.string().optional(),
  sourceEvidenceId: z.string().optional(),
});

const matchResultSchema = z.object({
  strong: z.array(matchItemSchema),
  weak: z.array(matchItemSchema),
  missing: z.array(matchItemSchema),
  risks: z.array(matchItemSchema),
});

const fitScoreSchema = z.object({
  total: z.number().min(0).max(100),
  categories: z.array(z.object({ label: z.string(), score: z.number(), reason: z.string() })),
});

const resumeSuggestionsSchema = z.object({
  bullets: z.array(z.string()),
  projectDescriptions: z.array(z.string()),
  skillPriority: z.array(z.string()),
  atsKeywords: z.array(z.string()),
});

const miniProjectRecommendationSchema = z.object({
  title: z.string(),
  goal: z.string(),
  targetGaps: z.array(z.string()),
  deliverables: z.array(z.string()),
  suggestedDurationDays: z.number(),
});

const interviewPrepSchema = z.object({
  questions: z.array(z.string()),
  weakAreas: z.array(z.string()),
  sevenDayPlan: z.array(z.string()),
});

const relatedSkillGuidanceSchema = z.object({
  skill: z.string(),
  relatedSkills: z.array(z.string()),
  reason: z.string(),
});

const retrievedContextItemSchema = z.object({
  chunkId: z.string(),
  sourceType: sourceTypeSchema,
  sourceRecordId: z.string(),
  text: z.string(),
  relevanceScore: z.number(),
  visibility: visibilitySchema,
  piiRisk: piiRiskSchema,
  reason: z.string(),
});

const retrievalContextSchema = z.object({
  enabled: z.boolean(),
  query: z.string(),
  items: z.array(retrievedContextItemSchema),
  provider: z.enum(["none", "mock", "pgvector", "managed_vector_db"]),
  filters: z.object({
    ownerUserId: z.string().optional(),
    visibility: z.array(visibilitySchema),
    sourceTypes: z.array(sourceTypeSchema),
    maxPiiRisk: piiRiskSchema,
  }),
});

const analysisMetadataSchema = z.object({
  schemaVersion: z.string(),
  promptVersion: z.string().optional(),
  modelVersion: z.string().optional(),
  scoringVersion: z.string(),
  retrievalUsed: z.boolean(),
  persisted: z.literal(false),
});

export const careerDiffAnalysisResultSchema = z.object({
  fitScore: fitScoreSchema,
  summary: z.string(),
  jobRequirements: jobRequirementsSchema,
  candidateEvidence: candidateEvidenceSchema,
  retrievalContext: retrievalContextSchema,
  matches: matchResultSchema,
  resumeSuggestions: resumeSuggestionsSchema,
  miniProjects: z.array(miniProjectRecommendationSchema),
  interviewPrep: interviewPrepSchema,
  relatedSkillGuidance: z.array(relatedSkillGuidanceSchema),
  metadata: analysisMetadataSchema,
});

/**
 * Backfills fields added to CareerDiffAnalysisResult after older saved
 * results (browser localStorage and data/*.json) were written, so those
 * legitimate past analyses validate instead of being discarded outright.
 * Only additive, safe-to-default fields belong here — relatedSkillGuidance
 * defaults to [] because "no known relation" is indistinguishable from "this
 * result predates the field". A renamed or removed field must fail
 * validation instead of being silently patched here.
 */
export function backfillLegacyAnalysisResult(raw: unknown): unknown {
  if (!raw || typeof raw !== "object") return raw;
  return { relatedSkillGuidance: [], ...raw };
}

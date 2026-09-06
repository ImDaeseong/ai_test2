/**
 * Shared analysis data contracts.
 *
 * Source of truth: ../../../../docs/ARCHITECTURE.md
 * Keep this file in sync with that document — update both together.
 */

export type Confidence = "high" | "medium" | "low";
export type ConsentBasis = "session_only" | "explicit_save" | "public_data" | "anonymized";
export type Visibility = "private" | "team" | "public_taxonomy" | "anonymized_aggregate";
export type PiiRisk = "low" | "medium" | "high";

export type JobDescriptionInput = {
  rawText: string;
  normalizedText: string;
  targetRole?: string;
  companyDomain?: string;
};

export type CandidateProfileInput = {
  rawText: string;
  normalizedText: string;
  targetSeniority?: string;
};

export type RequirementItem = {
  id: string;
  label: string;
  category: string;
  evidenceSnippet?: string;
  confidence: Confidence;
  sourceRecordId?: string;
};

export type JobRequirements = {
  requiredSkills: RequirementItem[];
  preferredSkills: RequirementItem[];
  domain: RequirementItem[];
  seniority?: string;
  collaboration: RequirementItem[];
  deliveryExpectations: RequirementItem[];
};

export type EvidenceItem = {
  id: string;
  label: string;
  sourceSnippet: string;
  confidence: Confidence;
  sourceRecordId?: string;
};

export type CandidateEvidence = {
  skills: EvidenceItem[];
  projects: EvidenceItem[];
  responsibilities: EvidenceItem[];
  achievements: EvidenceItem[];
  collaboration: EvidenceItem[];
};

export type MatchItem = {
  requirement: string;
  status: "strong" | "weak" | "missing" | "risk";
  reason: string;
  evidenceSnippet?: string;
  sourceRequirementId?: string;
  sourceEvidenceId?: string;
};

export type MatchResult = {
  strong: MatchItem[];
  weak: MatchItem[];
  missing: MatchItem[];
  risks: MatchItem[];
};

export type FitScore = {
  total: number;
  categories: Array<{ label: string; score: number; reason: string }>;
};

export type ResumeSuggestions = {
  bullets: string[];
  projectDescriptions: string[];
  skillPriority: string[];
  atsKeywords: string[];
};

export type MiniProjectRecommendation = {
  title: string;
  goal: string;
  targetGaps: string[];
  deliverables: string[];
  suggestedDurationDays: number;
};

export type InterviewPrep = {
  questions: string[];
  weakAreas: string[];
  sevenDayPlan: string[];
};

export type RelatedSkillGuidance = {
  /** A missing or weak requirement this guidance addresses. */
  skill: string;
  /** Other skills in the taxonomy that this skill builds on or connects to. */
  relatedSkills: string[];
  /** Why these skills are related, so the recommendation is grounded, not free-associated. */
  reason: string;
};

// --- RAG-ready contracts (base design; MVP keeps retrievalContext.enabled=false, provider="none") ---

export type EmbeddableChunk = {
  id: string;
  ownerUserId?: string;
  sourceType: "job_requirement" | "candidate_evidence" | "project_evidence" | "skill_taxonomy" | "analysis_summary";
  visibility: Visibility;
  textForEmbedding: string;
  sourceRecordId: string;
  sourceField: string;
  piiRisk: PiiRisk;
  consentBasis: ConsentBasis;
  schemaVersion: string;
  createdAt: string;
};

export type RetrievedContextItem = {
  chunkId: string;
  sourceType: EmbeddableChunk["sourceType"];
  sourceRecordId: string;
  text: string;
  relevanceScore: number;
  visibility: Visibility;
  piiRisk: PiiRisk;
  reason: string;
};

export type RetrievalContext = {
  enabled: boolean;
  query: string;
  items: RetrievedContextItem[];
  provider: "none" | "mock" | "pgvector" | "managed_vector_db";
  filters: {
    ownerUserId?: string;
    visibility: Visibility[];
    sourceTypes: EmbeddableChunk["sourceType"][];
    maxPiiRisk: PiiRisk;
  };
};

export type AnalysisMetadata = {
  schemaVersion: string;
  promptVersion?: string;
  modelVersion?: string;
  scoringVersion: string;
  retrievalUsed: boolean;
  persisted: boolean;
};

export type CareerDiffAnalysisResult = {
  fitScore: FitScore;
  summary: string;
  jobRequirements: JobRequirements;
  candidateEvidence: CandidateEvidence;
  retrievalContext: RetrievalContext;
  matches: MatchResult;
  resumeSuggestions: ResumeSuggestions;
  miniProjects: MiniProjectRecommendation[];
  interviewPrep: InterviewPrep;
  relatedSkillGuidance: RelatedSkillGuidance[];
  metadata: AnalysisMetadata;
};

// --- API contract (source of truth: docs/ARCHITECTURE.md, docs/ARCHITECTURE.md) ---

export type AnalyzeRequest = {
  jobDescription: string;
  candidateProfile: string;
  targetRole?: string;
  targetSeniority?: string;
  retrieval?: {
    enabled: boolean;
    includeSavedEvidence?: boolean;
    includePublicTaxonomy?: boolean;
    includeHistoricalAnalyses?: boolean;
  };
};

export type AnalyzeResponse = {
  result: CareerDiffAnalysisResult;
  privacy: {
    persisted: false;
    rawInputLogged: false;
    retrievalUsed: boolean;
  };
};

export type ApiErrorResponse = {
  error: {
    code: "VALIDATION_ERROR" | "ANALYSIS_FAILED" | "PROVIDER_TIMEOUT" | "RATE_LIMITED" | "PRIVACY_BLOCKED";
    message: string;
    retryable: boolean;
  };
};

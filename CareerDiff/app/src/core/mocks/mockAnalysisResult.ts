import type { CareerDiffAnalysisResult } from "@/core/types";

/**
 * A stable, fully-synthetic analysis result used as a shared test fixture
 * (dashboard rendering, schema, and provider tests). Not used at runtime — the
 * no-key path runs the deterministic local analyzer, not this mock.
 */
export const mockAnalysisResult: CareerDiffAnalysisResult = {
  fitScore: {
    total: 68,
    categories: [
      { label: "필수 스킬", score: 72, reason: "필수 스킬 4개 중 3개에서 직접적인 근거가 확인됩니다." },
      { label: "우대 스킬", score: 55, reason: "우대 스킬 3개 중 1개에서 직접적인 근거가 확인됩니다." },
      { label: "도메인 적합도", score: 80, reason: "지원자가 직접 관련된 도메인에서 2년간 경력이 있습니다." },
      { label: "시니어리티 적합도", score: 60, reason: "지원자의 담당 범위가 목표 레벨보다 다소 좁습니다." },
    ],
  },
  summary:
    "백엔드 기본기와 관련 도메인 경험은 탄탄하지만, 필수 요건인 클라우드 인프라 실무 경험 근거가 부족하고 목표 시니어리티에 맞는 리더십 사례가 명확하지 않습니다.",
  jobRequirements: {
    requiredSkills: [
      { id: "req-1", label: "TypeScript", category: "language", confidence: "high" },
      { id: "req-2", label: "Node.js 백엔드 서비스", category: "framework", confidence: "high" },
      { id: "req-3", label: "PostgreSQL", category: "database", confidence: "high" },
      { id: "req-4", label: "AWS (ECS/Lambda)", category: "infrastructure", confidence: "medium" },
    ],
    preferredSkills: [
      { id: "pref-1", label: "GraphQL API 설계", category: "framework", confidence: "medium" },
      { id: "pref-2", label: "Terraform", category: "infrastructure", confidence: "low" },
      { id: "pref-3", label: "주니어 엔지니어 멘토링", category: "leadership", confidence: "medium" },
    ],
    domain: [{ id: "dom-1", label: "B2B SaaS", category: "domain", confidence: "high" }],
    seniority: "미드~시니어",
    collaboration: [{ id: "collab-1", label: "제품/디자인과의 교차 기능 협업", category: "collaboration", confidence: "medium" }],
    deliveryExpectations: [{ id: "del-1", label: "서비스 단독 오너십", category: "delivery", confidence: "medium" }],
  },
  candidateEvidence: {
    skills: [
      { id: "ev-1", label: "TypeScript", sourceSnippet: "TypeScript로 백엔드 서비스를 2년간 구축·운영했습니다.", confidence: "high" },
      { id: "ev-2", label: "Node.js", sourceSnippet: "피크 시 초당 500건 요청을 처리하는 Node.js/Express API를 운영했습니다.", confidence: "high" },
      { id: "ev-3", label: "PostgreSQL", sourceSnippet: "PostgreSQL 기반 리포팅 서비스의 스키마 설계와 쿼리 최적화를 진행했습니다.", confidence: "high" },
    ],
    projects: [
      { id: "ev-4", label: "내부 리포팅 플랫폼", sourceSnippet: "내부 사용자 40명 이상이 쓰는 리포팅 플랫폼의 백엔드 재작성을 주도했습니다.", confidence: "high" },
    ],
    responsibilities: [
      { id: "ev-5", label: "서비스 오너십", sourceSnippet: "빌링 서비스를 설계 단계부터 온콜 대응까지 단독으로 책임졌습니다.", confidence: "medium" },
    ],
    achievements: [
      { id: "ev-6", label: "지연시간 개선", sourceSnippet: "쿼리 최적화를 통해 API p95 지연시간을 35% 줄였습니다.", confidence: "high" },
    ],
    collaboration: [
      { id: "ev-7", label: "제품 협업", sourceSnippet: "분기 로드맵 항목 범위를 정하기 위해 제품 매니저와 직접 협업했습니다.", confidence: "medium" },
    ],
  },
  retrievalContext: {
    enabled: false,
    query: "",
    items: [],
    provider: "none",
    filters: {
      visibility: ["private"],
      sourceTypes: [],
      maxPiiRisk: "low",
    },
  },
  matches: {
    strong: [
      { requirement: "TypeScript", status: "strong", reason: "2년간 실무 프로덕션 TypeScript 경험이 직접 확인됩니다.", evidenceSnippet: "TypeScript로 백엔드 서비스를 2년간 구축·운영했습니다." },
      { requirement: "Node.js 백엔드 서비스", status: "strong", reason: "프로덕션 Node.js 서비스를 단독으로 책임진 경험이 있습니다.", evidenceSnippet: "피크 시 초당 500건 요청을 처리하는 Node.js/Express API를 운영했습니다." },
      { requirement: "PostgreSQL", status: "strong", reason: "직접적인 스키마 설계와 쿼리 최적화 경험이 있습니다.", evidenceSnippet: "PostgreSQL 기반 리포팅 서비스의 스키마 설계와 쿼리 최적화를 진행했습니다." },
    ],
    weak: [
      { requirement: "GraphQL API 설계", status: "weak", reason: "직접 근거는 없지만, REST API 설계 경험이 강해서 어느 정도 대체 근거가 됩니다." },
    ],
    missing: [
      { requirement: "AWS (ECS/Lambda)", status: "missing", reason: "제공된 프로필에서 클라우드 인프라 관련 근거를 찾지 못했습니다." },
      { requirement: "Terraform", status: "missing", reason: "인프라 코드화(IaC) 관련 근거를 찾지 못했습니다." },
    ],
    risks: [
      { requirement: "주니어 엔지니어 멘토링", status: "risk", reason: "채용공고상 이 시니어리티에서는 멘토링 역할이 기대되는데, 관련 근거가 제공되지 않았습니다." },
    ],
  },
  resumeSuggestions: {
    bullets: [
      "빌링 서비스를 설계부터 구현, 온콜 대응까지 단독으로 책임졌고, 쿼리 최적화로 API p95 지연시간을 35% 줄였습니다.",
      "내부 사용자 40명 이상이 쓰는 리포팅 플랫폼의 백엔드 재작성을 주도해 PostgreSQL 기반 아키텍처로 전환했습니다.",
    ],
    projectDescriptions: [
      "내부 리포팅 플랫폼 — TypeScript/Node.js/PostgreSQL 기반 서비스로 내부 사용자 40명 이상 지원, 백엔드 재작성 주도 및 스키마 설계 담당.",
    ],
    skillPriority: ["AWS (ECS/Lambda)", "Terraform", "GraphQL API 설계"],
    atsKeywords: ["TypeScript", "Node.js", "PostgreSQL", "API 설계", "온콜", "서비스 오너십"],
  },
  miniProjects: [
    {
      title: "Terraform으로 소규모 Node.js 서비스를 AWS ECS에 배포",
      goal: "구체적이고 시연 가능한 결과물로 AWS/Terraform 근거 공백을 메웁니다.",
      targetGaps: ["AWS (ECS/Lambda)", "Terraform"],
      deliverables: ["ECS 서비스용 Terraform 구성", "아키텍처 결정을 설명하는 짧은 README", "이력서에 추가할 공개 저장소 링크"],
      suggestedDurationDays: 5,
    },
    {
      title: "기존 REST API 앞에 소규모 GraphQL 레이어 추가",
      goal: "강한 REST API 설계 경험을 직접적인 GraphQL 근거로 전환합니다.",
      targetGaps: ["GraphQL API 설계"],
      deliverables: ["기존 REST 리소스 2~3개에 대한 GraphQL 스키마", "REST/GraphQL 버전을 비교하는 짧은 글"],
      suggestedDurationDays: 3,
    },
    {
      title: "짧은 사내 기술 발표 또는 멘토링 문서 작성 및 발표",
      goal: "참조 가능한 구체적인 멘토링/리더십 결과물을 만듭니다.",
      targetGaps: ["주니어 엔지니어 멘토링"],
      deliverables: ["주니어 엔지니어 대상 기술 개념 설명 녹화 또는 문서", "이력서에 추가할 한 문단 요약"],
      suggestedDurationDays: 2,
    },
  ],
  interviewPrep: {
    questions: [
      "단독으로 책임진 빌링 서비스를 어떻게 설계했는지 설명해 주세요.",
      "느린 쿼리를 최적화한 경험을 말씀해 주세요 — 병목 지점을 어떻게 찾으셨나요?",
      "Node.js 서비스를 처음 AWS에 배포한다면 어떻게 접근하시겠어요?",
    ],
    weakAreas: ["클라우드 인프라 (AWS/Terraform)", "멘토링/리더십 사례"],
    sevenDayPlan: [
      "1~2일차: AWS/Terraform 보완 프로젝트 진행.",
      "3일차: 위 제안을 참고해 이력서 불릿 재작성.",
      "4일차: 면접 예상 질문 3개에 대한 STAR 형식 답변 준비.",
      "5일차: 과거 팀 협업 경험 중 멘토링/리더십 스토리 하나 정리.",
      "6~7일차: 시스템 설계와 약점 영역 위주로 모의 면접 진행.",
    ],
  },
  relatedSkillGuidance: [
    {
      skill: "AWS (ECS/Lambda)",
      relatedSkills: ["Docker", "Kubernetes"],
      reason:
        "AWS (ECS/Lambda)은 Docker, Kubernetes과 연결된 기술입니다. 관련 기술부터 함께 준비하면 학습 경로를 좁힐 수 있습니다.",
    },
  ],
  metadata: {
    schemaVersion: "1.0.0",
    scoringVersion: "mock-0.1.0",
    retrievalUsed: false,
    persisted: false,
  },
};

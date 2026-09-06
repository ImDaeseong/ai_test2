import type { AnalyzeRequestInput } from "@/core/schemas/analyzeRequest";
import type {
  CareerDiffAnalysisResult,
  EvidenceItem,
  MatchItem,
  RelatedSkillGuidance,
  RequirementItem,
} from "@/core/types";

type SkillDefinition = {
  label: string;
  category: string;
  aliases: string[];
  /**
   * Labels of other SKILLS entries this one builds on or connects to (a
   * lightweight ontology relation, not a free-text guess). Only set where the
   * relationship is a well-established technical fact — most entries have none.
   */
  relatedTo?: string[];
};

const SKILLS: SkillDefinition[] = [
  { label: "Python", category: "language", aliases: ["python"] },
  { label: "Java", category: "language", aliases: ["java"] },
  { label: "Kotlin", category: "language", aliases: ["kotlin"], relatedTo: ["Java"] },
  { label: "TypeScript", category: "language", aliases: ["typescript"], relatedTo: ["JavaScript"] },
  { label: "JavaScript", category: "language", aliases: ["javascript"] },
  { label: "FastAPI", category: "framework", aliases: ["fastapi"], relatedTo: ["Python"] },
  { label: "Django", category: "framework", aliases: ["django"], relatedTo: ["Python"] },
  { label: "Flask", category: "framework", aliases: ["flask"], relatedTo: ["Python"] },
  { label: "Spring", category: "framework", aliases: ["spring"], relatedTo: ["Java"] },
  { label: "Node.js", category: "framework", aliases: ["node.js", "nodejs"], relatedTo: ["JavaScript"] },
  { label: "React", category: "framework", aliases: ["react"], relatedTo: ["JavaScript"] },
  { label: "Next.js", category: "framework", aliases: ["next.js", "nextjs"], relatedTo: ["React"] },
  { label: "SQL", category: "database", aliases: ["sql"] },
  { label: "PostgreSQL", category: "database", aliases: ["postgresql", "postgres"], relatedTo: ["SQL"] },
  { label: "MySQL", category: "database", aliases: ["mysql"], relatedTo: ["SQL"] },
  { label: "MS SQL Server", category: "database", aliases: ["mssql", "ms-sql", "sql server"], relatedTo: ["SQL"] },
  { label: "MariaDB", category: "database", aliases: ["mariadb"], relatedTo: ["SQL"] },
  { label: "Redis", category: "database", aliases: ["redis"] },
  { label: "MongoDB", category: "database", aliases: ["mongodb"] },
  { label: "Elasticsearch", category: "database", aliases: ["elasticsearch"] },
  { label: "AWS", category: "infrastructure", aliases: ["aws", "amazon web services"] },
  { label: "GCP", category: "infrastructure", aliases: ["gcp", "google cloud"] },
  { label: "Azure", category: "infrastructure", aliases: ["azure"] },
  { label: "Docker", category: "infrastructure", aliases: ["docker"], relatedTo: ["Kubernetes"] },
  { label: "Kubernetes", category: "infrastructure", aliases: ["kubernetes", "k8s"], relatedTo: ["Docker"] },
  { label: "Terraform", category: "infrastructure", aliases: ["terraform"] },
  { label: "GitHub Actions", category: "delivery", aliases: ["github actions"], relatedTo: ["CI/CD"] },
  { label: "CI/CD", category: "delivery", aliases: ["ci/cd", "cicd"], relatedTo: ["GitHub Actions"] },
  { label: "REST API", category: "api", aliases: ["rest api", "restful"] },
  { label: "GraphQL", category: "api", aliases: ["graphql"] },
  { label: "Kafka", category: "messaging", aliases: ["kafka"] },
  { label: "RabbitMQ", category: "messaging", aliases: ["rabbitmq"] },
  { label: "Airflow", category: "data", aliases: ["airflow"], relatedTo: ["Spark", "Python"] },
  { label: "Spark", category: "data", aliases: ["spark"] },
  { label: "PyTorch", category: "ai", aliases: ["pytorch"], relatedTo: ["CUDA", "Python"] },
  { label: "TensorFlow", category: "ai", aliases: ["tensorflow"], relatedTo: ["CUDA", "Python"] },
  { label: "LangChain", category: "ai", aliases: ["langchain"], relatedTo: ["LLM"] },
  { label: "LangGraph", category: "ai", aliases: ["langgraph"], relatedTo: ["LangChain"] },
  { label: "RAG", category: "ai", aliases: ["rag", "retrieval augmented"], relatedTo: ["Vector DB", "LangChain", "LLM"] },
  { label: "LLM", category: "ai", aliases: ["llm", "large language model"], relatedTo: ["OpenAI"] },
  { label: "OpenAI", category: "ai", aliases: ["openai", "gpt"] },
  { label: "Embedding", category: "ai", aliases: ["embedding", "임베딩"], relatedTo: ["Vector DB"] },
  {
    label: "Vector DB",
    category: "ai",
    aliases: ["vector db", "vector database", "벡터 db", "벡터 데이터베이스"],
    relatedTo: ["Embedding"],
  },
  { label: "Unreal Engine", category: "simulation", aliases: ["unreal engine", "unreal", "언리얼"], relatedTo: ["C++"] },
  { label: "Unity", category: "simulation", aliases: ["unity3d", "unity"], relatedTo: ["C#"] },
  { label: "WebGL", category: "simulation", aliases: ["webgl"] },
  { label: "WebGPU", category: "simulation", aliases: ["webgpu"], relatedTo: ["WebGL"] },
  {
    label: "VLA",
    category: "ai",
    aliases: ["vla", "vision-language-action"],
    relatedTo: ["Reinforcement Learning", "Computer Vision"],
  },
  {
    label: "Reinforcement Learning",
    category: "ai",
    aliases: ["reinforcement learning", "강화학습"],
    relatedTo: ["Sim2Real"],
  },
  { label: "Sim2Real", category: "simulation", aliases: ["sim2real"], relatedTo: ["Reinforcement Learning", "Digital Twin"] },
  {
    label: "Digital Twin",
    category: "simulation",
    aliases: ["digital twin", "디지털 트윈"],
    relatedTo: ["Unreal Engine", "Unity"],
  },
  { label: "Playwright", category: "testing", aliases: ["playwright"] },
  { label: "Selenium", category: "testing", aliases: ["selenium"] },
  { label: "BeautifulSoup", category: "collection", aliases: ["beautifulsoup", "beautiful soup"], relatedTo: ["Python"] },
  // Added from real postings (C++/C#/Flutter/HTML/CSS/QA/DevOps were present but
  // unmatched) plus common languages/frameworks that were missing. Aliases are
  // kept substring-safe on purpose — e.g. no bare "go"/"뷰"/"rust", which would
  // falsely match 하고/인터뷰/cluster.
  { label: "C++", category: "language", aliases: ["c++"] },
  { label: "C#", category: "language", aliases: ["c#"] },
  { label: "Go", category: "language", aliases: ["golang"] },
  { label: "Swift", category: "language", aliases: ["swift"] },
  { label: "PHP", category: "language", aliases: ["php"] },
  { label: "Vue.js", category: "framework", aliases: ["vue.js", "vuejs", "vue"], relatedTo: ["JavaScript"] },
  { label: "Angular", category: "framework", aliases: ["angular"], relatedTo: ["TypeScript"] },
  { label: "Flutter", category: "framework", aliases: ["flutter", "플러터"] },
  { label: "HTML", category: "frontend", aliases: ["html"] },
  { label: "CSS", category: "frontend", aliases: ["css"] },
  { label: "DevOps", category: "delivery", aliases: ["devops"], relatedTo: ["CI/CD"] },
  { label: "QA", category: "testing", aliases: ["qa"] },
  // Robotics/hardware domain, added from real CTO/로봇 postings. Aliases stay
  // substring-safe — no bare "ros" (across), "imu" (simulation), or "제어"
  // (원격제어), which would false-match.
  { label: "Robotics", category: "robotics", aliases: ["로봇", "로보틱스", "robotics"], relatedTo: ["ROS", "Embedded"] },
  { label: "Mechatronics", category: "robotics", aliases: ["메카트로닉스", "mechatronics"] },
  { label: "Autonomous Driving", category: "robotics", aliases: ["자율주행", "autonomous driving"] },
  { label: "ROS", category: "robotics", aliases: ["ros2", "ros 2", "robot operating system"], relatedTo: ["Robotics"] },
  { label: "Embedded", category: "hardware", aliases: ["embedded", "임베디드"], relatedTo: ["Firmware", "MCU"] },
  { label: "Firmware", category: "hardware", aliases: ["firmware", "펌웨어"], relatedTo: ["Embedded", "MCU"] },
  { label: "Computer Vision", category: "ai", aliases: ["computer vision", "컴퓨터 비전", "컴퓨터비전"], relatedTo: ["PyTorch", "TensorFlow"] },
  { label: "CUDA", category: "ai", aliases: ["cuda"], relatedTo: ["PyTorch", "TensorFlow"] },
  // Added from a real 로봇제어/강화학습 posting (C, Linux, CATIA, NX, OrCAD,
  // CUDA, MCU, Embedded, SIMD listed as required 스킬) that a local-analyzer
  // run left mostly unmatched. Bare "NX" is skipped as unsafe (2-char substring).
  { label: "Linux", category: "infrastructure", aliases: ["linux", "리눅스"] },
  { label: "CATIA", category: "hardware", aliases: ["catia"] },
  { label: "OrCAD", category: "hardware", aliases: ["orcad"] },
  { label: "MCU", category: "hardware", aliases: ["mcu"], relatedTo: ["Embedded", "Firmware"] },
  { label: "SIMD", category: "hardware", aliases: ["simd"] },
  // Added from a real "C# WPF 개발자" posting where a 47-case batch test run
  // left WPF unmatched. CIM/HCM from the same 스킬 line were skipped as
  // ambiguous ERP-module acronyms, not identifiable developer skills.
  { label: "WPF", category: "framework", aliases: ["wpf"], relatedTo: ["C#"] },
  // Added from a real posting (스킬: C, C#, C++, Delphi, JAVA, MSSQL, DBMS) that
  // left Delphi and MSSQL unmatched despite the other four already being known.
  // "DBMS" was skipped as a generic category label, not an identifiable single
  // technology (same reasoning that skipped CIM/HCM above).
  { label: "Delphi", category: "language", aliases: ["delphi"] },
];

// Ontology pass over existing entries (94-case validation review, 2026-08):
// several framework/library skills had no `relatedTo` link back to the base
// language they run on, so a candidate who only listed the base language got
// no bridge toward the missing framework. Each addition below is a
// well-established, undebatable technical fact — a framework/library's own
// runtime or primary implementation language — not a guess:
//   FastAPI/Django/Flask → Python (Python web frameworks)
//   Spring → Java (Java framework); Kotlin → Java (JVM-interop, officially
//     co-supported for Android/backend)
//   PyTorch/TensorFlow → added Python alongside existing CUDA (both are
//     Python-first ML frameworks)
//   RAG → added LLM alongside existing Vector DB/LangChain (RAG's own
//     definition — Retrieval-Augmented *Generation* — augments an LLM)
//   WebGPU → WebGL (WebGPU is the browser vendors' documented successor to
//     WebGL, not an unrelated API)
// No certifications or course names were added, per docs/ARCHITECTURE.md.
//
// Second pass (2026-08-18): more base-language/runtime links plus two new
// skills evidenced by a real posting (스킬: C, C#, C++, Delphi, JAVA, MSSQL,
// DBMS — see the Delphi entry's comment above):
//   TypeScript → JavaScript (TypeScript is a typed superset that compiles to
//     JavaScript); Node.js/React/Vue.js → JavaScript; Angular → TypeScript
//     (Angular is written in and requires TypeScript)
//   Unity → C#; Unreal Engine → C++ (each engine's official primary
//     scripting/native language)
//   BeautifulSoup → Python (it is a Python library, not multi-language)
//   Airflow → added Python alongside existing Spark (Airflow DAGs are
//     authored in Python)
//   MS SQL Server, MariaDB → SQL (same relatedTo pattern as the existing
//     PostgreSQL/MySQL → SQL entries; MariaDB had no direct posting evidence
//     this pass but is a common, unambiguous database like its MySQL sibling)

const FALLBACK_GAPS = ["요구사항 기반 API 구현", "자동화 테스트", "배포 및 운영 문서화"];

// Used for both fitScore categories when there is no comparable skill signal
// (no detected posting skills, or no matched evidence), so an unrelated
// posting (e.g. business-ops lead vs. a software résumé) doesn't read as a
// flattering ~40% match while the risk banner says the opposite.
const NO_SIGNAL_SCORE = 20;

// A missing skill's direct relatedTo neighbors sometimes have no relatedTo of
// their own back to something the candidate holds (e.g. LangGraph->LangChain
// ends there, but LangChain->LLM->OpenAI continues). MAX_BRIDGE_DEPTH bounds
// how many relatedTo hops findBridgePath will walk past the direct neighbors
// before giving up, so a lookup can't wander the whole graph.
const MAX_BRIDGE_DEPTH = 3;

/**
 * Breadth-first search over the relatedTo graph, starting from a missing
 * skill's direct neighbors, for the nearest skill the candidate already has
 * evidence for. Returns the hop path from that candidate skill back to
 * (but not including) `skillLabel`, or null if none is found within
 * MAX_BRIDGE_DEPTH hops.
 */
function findBridgePath(skillLabel: string, candidateProfile: string): string[] | null {
  const start = SKILLS.find((skill) => skill.label === skillLabel);
  if (!start) return null;

  const visited = new Set<string>([skillLabel]);
  let frontier: { label: string; path: string[] }[] = (start.relatedTo ?? []).map((label) => ({
    label,
    path: [label],
  }));

  for (let depth = 0; depth < MAX_BRIDGE_DEPTH && frontier.length > 0; depth++) {
    const nextFrontier: typeof frontier = [];
    for (const node of frontier) {
      if (visited.has(node.label)) continue;
      visited.add(node.label);
      const skill = SKILLS.find((candidate) => candidate.label === node.label);
      if (!skill) continue;
      if (includesSkill(candidateProfile, skill)) {
        return [...node.path].reverse();
      }
      for (const next of skill.relatedTo ?? []) {
        if (!visited.has(next)) nextFrontier.push({ label: next, path: [...node.path, next] });
      }
    }
    frontier = nextFrontier;
  }
  return null;
}

const ASCII_ALIAS_PATTERN = /^[\x00-\x7f]+$/;

function includesSkill(text: string, skill: SkillDefinition): boolean {
  const lower = text.toLowerCase();
  return skill.aliases.some((alias) => {
    const lowerAlias = alias.toLowerCase();
    if (!ASCII_ALIAS_PATTERN.test(lowerAlias)) {
      // Korean aliases have no Latin word-boundary concept; keep plain
      // substring matching, as the existing entries are already curated to
      // be substring-safe (see the SKILLS comments above).
      return lower.includes(lowerAlias);
    }
    // ASCII aliases must not be embedded inside a larger word — e.g. the
    // "html" alias previously matched inside "Dhtml" (1990s DHTML, not
    // modern HTML/CSS), falsely reporting a strong skill match. A trailing
    // version digit (e.g. "html5", "css3") still counts as the same skill.
    const escaped = lowerAlias.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return new RegExp(`(?<![a-z0-9])${escaped}(?![a-z])`, "i").test(lower);
  });
}

export type AnalysisReadiness = {
  /** True only when this analyzer can produce a non-empty analysis. */
  ready: boolean;
  detectedSkills: string[];
  reason?: "too-short" | "no-known-skills";
};

const MIN_ANALYZABLE_LENGTH = 30;

/**
 * The analyzer's own judgment of whether a job description will produce a
 * usable analysis. It is the single source of truth for readiness: the
 * importer delegates here instead of guessing from text markers, so a
 * requirements heading with no recognizable skill is correctly not ready
 * (it would still yield an empty analysis). When the analyzer changes (e.g.
 * an LLM provider), this readiness logic changes with it.
 */
export function inspectJobDescription(description: string): AnalysisReadiness {
  const detectedSkills = SKILLS.filter((skill) => includesSkill(description, skill)).map((skill) => skill.label);
  if (description.trim().length < MIN_ANALYZABLE_LENGTH) {
    return { ready: false, detectedSkills, reason: "too-short" };
  }
  if (detectedSkills.length === 0) {
    return { ready: false, detectedSkills, reason: "no-known-skills" };
  }
  return { ready: true, detectedSkills };
}

function evidenceSnippet(text: string, skill: SkillDefinition): string {
  const line = text
    .split(/\r?\n/)
    .find((candidate) => includesSkill(candidate, skill))
    ?.trim();
  return (line || `${skill.label} 관련 내용이 후보자 프로필에 포함되어 있습니다.`).slice(0, 240);
}

function requirement(skill: SkillDefinition, index: number, prefix: string): RequirementItem {
  return {
    id: `${prefix}-${index + 1}`,
    label: skill.label,
    category: skill.category,
    confidence: "high",
  };
}

/**
 * Extracts 경력/학력/우대조건 from the 잡코리아-style "지원자격" block that most
 * postings share, regardless of whether SKILLS recognizes any tech keyword in
 * the text. A non-dev posting (QA/제조/영업 등) still has these fields, so this
 * is what keeps jobRequirements.domain from going empty on every posting
 * outside the SKILLS taxonomy's coverage — see LocalAnalysisProvider.test.ts
 * for the real postings (다이캐스팅 품질, 자동차 렌트 CTO) that exposed the gap.
 * Heuristic pattern matching over free text, so confidence stays "medium".
 */
function extractDomainRequirements(jobDescription: string): RequirementItem[] {
  const items: RequirementItem[] = [];
  const push = (label: string, category: string) => {
    items.push({ id: `domain-${items.length + 1}`, label, category, confidence: "medium" });
  };

  // Two jobkorea layouts have been seen in real postings: "경력\n경력\n(N년이상)"
  // (parenthesized value on its own line) and "경력\n경력(N년이상)" (no newline
  // before the parenthesis, mobile layout) — the \n? keeps both matching.
  // "경력무관" is a third literal value (no parentheses) alongside "신입·경력".
  const careerMatch = jobDescription.match(/경력\s*\n\s*(신입[·・]경력|경력무관|경력\s*\n?\s*\(([^)]+)\))/);
  if (careerMatch) {
    push(careerMatch[2] ? `경력 ${careerMatch[2]}` : careerMatch[1], "experience");
  }

  // A parenthesized qualifier ("(졸업예정자 가능)", "(직무별 상이)") sometimes
  // wraps onto its own following line rather than staying on the 학력 value
  // line (real-data check: 10/161 stored postings) — fold it back in so it
  // isn't silently dropped.
  const educationMatch = jobDescription.match(/학력\s*\n\s*([^\n]+)\n?(\([^\n]*\))?/);
  if (educationMatch) {
    const value = [educationMatch[1].trim(), educationMatch[2]?.trim()].filter(Boolean).join(" ");
    push(`학력 ${value}`, "education");
  }

  // Real-data regression: a posting whose free-text title ended in "...경험
  // 우대\n⭐ 158명 이상 찜한 기업" made this match on that sentence's "우대"
  // instead of the actual "우대조건" heading further down, capturing the
  // company-interest banner as a fake preferred condition and silently
  // dropping the real 우대조건 list. Anchoring to line-start (the heading is
  // always alone on its own line) rules out a "우대" that ends a sentence.
  const preferredMatch = jobDescription.match(/(?:^|\n)우대(?:조건)?\s*\n\s*(?:기본우대\s*\n)?\s*([^\n]+)/);
  if (preferredMatch) {
    for (const condition of preferredMatch[1].split(",").map((entry) => entry.trim()).filter(Boolean)) {
      push(condition, "preferred");
    }
  }

  return items;
}

export function buildLocalAnalysis(input: AnalyzeRequestInput): CareerDiffAnalysisResult {
  const preferredMarker = input.jobDescription.search(/우대|preferred|plus/i);
  const detected = SKILLS.filter((skill) => includesSkill(input.jobDescription, skill));
  const required = detected.filter((skill) => {
    if (preferredMarker < 0) return true;
    const first = Math.min(
      ...skill.aliases
        .map((alias) => input.jobDescription.toLowerCase().indexOf(alias))
        .filter((index) => index >= 0),
    );
    return first < preferredMarker;
  });
  const preferred = detected.filter((skill) => !required.includes(skill));
  const matched = detected.filter((skill) => includesSkill(input.candidateProfile, skill));
  const missing = detected.filter((skill) => !matched.includes(skill));
  const denominator = detected.length || 1;
  const score = detected.length ? Math.round((matched.length / denominator) * 100) : NO_SIGNAL_SCORE;

  const evidence: EvidenceItem[] = matched.map((skill, index) => ({
    id: `evidence-${index + 1}`,
    label: skill.label,
    sourceSnippet: evidenceSnippet(input.candidateProfile, skill),
    confidence: "high",
  }));
  const strong: MatchItem[] = matched.map((skill, index) => ({
    requirement: skill.label,
    status: "strong",
    reason: `후보자 프로필에서 ${skill.label} 관련 직접 근거가 확인됩니다.`,
    evidenceSnippet: evidence[index].sourceSnippet,
    sourceEvidenceId: evidence[index].id,
  }));
  const missingMatches: MatchItem[] = missing.map((skill) => ({
    requirement: skill.label,
    status: "missing",
    reason: `후보자 프로필에서 ${skill.label} 관련 근거를 찾지 못했습니다.`,
  }));
  // FALLBACK_GAPS is only for the no-signal case (nothing recognized in the
  // posting at all). A full match — real requirements detected and every one
  // satisfied — is a different, positive outcome and must not reuse the
  // no-signal fallback, or every downstream section (mini projects, resume
  // suggestions, interview prep, related-skill guidance) ends up inventing
  // gaps that don't exist.
  const hasFullMatch = detected.length > 0 && missing.length === 0;
  const gaps = missing.length ? missing.map((skill) => skill.label) : hasFullMatch ? [] : FALLBACK_GAPS;
  // Mini projects and the resume/interview copy below still need exactly
  // three focus items even on a full match, so fall back to the candidate's
  // own matched skills there — framed as deepening existing evidence, not
  // filling a gap (see gapProjectTitle/Goal/Description).
  const projectFocus = gaps.length ? gaps : matched.map((skill) => skill.label);
  const projectGaps = Array.from({ length: 3 }, (_, index) => projectFocus[index % projectFocus.length]);
  const gapProjectTitle = (focus: string, index: number) =>
    hasFullMatch ? `${focus} 심화 프로젝트 ${index + 1}` : `${focus} 검증 프로젝트 ${index + 1}`;
  const gapProjectGoal = (focus: string) =>
    hasFullMatch
      ? `이미 보유한 ${focus} 경험을 더 구체적인 성과로 발전시킵니다.`
      : `${focus}에 대한 직접적인 구현 근거를 만듭니다.`;
  const gapProjectDescription = (focus: string) =>
    hasFullMatch
      ? `${focus} 심화 프로젝트의 문제, 구현, 테스트, 결과를 한 문단으로 정리해 이력서에 구체적 성과로 남기세요.`
      : `${focus} 보완 프로젝트의 문제, 구현, 테스트, 결과를 한 문단으로 정리하세요.`;

  // A lightweight ontology pass over every gap — `gaps`, not `missing`, so
  // this covers the no-signal case too (an unrelated posting where zero
  // skills were even recognized, so miniProjects/resumeSuggestions/
  // interviewPrep fall back to FALLBACK_GAPS). On a full match, `gaps` is
  // correctly empty, so this naturally yields no entries too — there is
  // nothing left to guide toward. When a relatedTo link exists, explain the
  // candidate already has a related skill, name it as a concrete starting
  // point. When no relation is known (including FALLBACK_GAPS labels, which
  // aren't in the SKILLS taxonomy at all), still emit guidance
  // (relatedSkills: []) pointing at the gap itself instead of silently
  // omitting it.
  const relatedSkillGuidance: RelatedSkillGuidance[] = gaps.map((gapLabel) => {
    const skill = SKILLS.find((candidate) => candidate.label === gapLabel);
    const relatedLabels = skill?.relatedTo ?? [];
    if (!skill || relatedLabels.length === 0) {
      return {
        skill: gapLabel,
        relatedSkills: [],
        reason: `${gapLabel}은 taxonomy에 연결된 상위/인접 기술이 없습니다. ${gapLabel}을 직접 다루는 미니 프로젝트나 학습 자료로 근거를 만드는 것이 가장 확실한 준비 방법입니다.`,
      };
    }
    const bridgeSkills = relatedLabels.filter((label) =>
      SKILLS.some((related) => related.label === label && includesSkill(input.candidateProfile, related)),
    );
    const bridgePath = bridgeSkills.length ? null : findBridgePath(skill.label, input.candidateProfile);
    const reason = bridgeSkills.length
      ? `${skill.label}은 ${relatedLabels.join(", ")}과 연결된 기술입니다. 후보자는 이미 ${bridgeSkills.join(", ")} 경험이 있어 ${skill.label} 학습의 출발점으로 활용할 수 있습니다.`
      : bridgePath
        ? `${skill.label}은 ${relatedLabels.join(", ")}과 연결된 기술입니다. 후보자의 ${bridgePath.join(" → ")} 경험이 ${skill.label}까지 이어지는 학습 경로가 될 수 있습니다.`
        : `${skill.label}은 ${relatedLabels.join(", ")}과 연결된 기술입니다. 관련 기술부터 함께 준비하면 학습 경로를 좁힐 수 있습니다.`;
    return { skill: skill.label, relatedSkills: relatedLabels, reason };
  });

  return {
    fitScore: {
      total: score,
      categories: [
        {
          label: "기술 요구사항 일치",
          score,
          reason: `공고에서 찾은 기술 ${detected.length}개 중 ${matched.length}개가 후보자 프로필에서 확인됩니다.`,
        },
        {
          label: "근거 충실도",
          score: matched.length ? Math.min(100, 50 + matched.length * 10) : NO_SIGNAL_SCORE,
          reason: `직접 인용 가능한 기술 근거 ${matched.length}개를 확인했습니다.`,
        },
      ],
    },
    summary: detected.length
      ? `공고 기술 ${detected.map((skill) => skill.label).join(", ")} 중 ${matched.length}개가 일치하고 ${missing.length}개는 근거가 부족합니다.`
      : "공고에서 알려진 기술 키워드를 충분히 추출하지 못했습니다. 공고 본문과 후보자 프로필을 직접 확인해 주세요.",
    jobRequirements: {
      requiredSkills: required.map((skill, index) => requirement(skill, index, "required")),
      preferredSkills: preferred.map((skill, index) => requirement(skill, index, "preferred")),
      domain: extractDomainRequirements(input.jobDescription),
      collaboration: [],
      deliveryExpectations: [],
    },
    candidateEvidence: {
      skills: evidence,
      projects: [],
      responsibilities: [],
      achievements: [],
      collaboration: [],
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
      strong,
      weak: [],
      missing: missingMatches,
      risks: detected.length
        ? []
        : [{ requirement: "기술 요구사항", status: "risk", reason: "공고에서 비교 가능한 기술 키워드를 추출하지 못했습니다." }],
    },
    resumeSuggestions: {
      bullets: matched.slice(0, 3).map((skill) => `${skill.label}을 활용한 프로젝트의 역할, 규모, 성과 수치를 이력서에 명시하세요.`),
      projectDescriptions: projectGaps.map((gap) => gapProjectDescription(gap)),
      skillPriority: gaps,
      atsKeywords: detected.map((skill) => skill.label),
    },
    miniProjects: projectGaps.map((gap, index) => ({
      title: gapProjectTitle(gap, index),
      goal: gapProjectGoal(gap),
      targetGaps: [gap],
      deliverables: ["실행 가능한 소스 코드", "자동화 테스트", "설계와 실행 방법을 설명하는 README"],
      suggestedDurationDays: 3,
    })),
    interviewPrep: {
      questions: detected.slice(0, 5).map((skill) => `${skill.label}을 실제 프로젝트에서 어떻게 사용했는지 설명해 주세요.`),
      weakAreas: gaps,
      sevenDayPlan: [
        `1일차: 공고 요구 기술 ${detected.map((skill) => skill.label).join(", ") || "원문"} 정리`,
        "2일차: 후보자 프로필의 직접 근거와 성과 수치 정리",
        `3~4일차: ${projectGaps[0]} ${hasFullMatch ? "심화" : "보완"} 프로젝트 구현`,
        "5일차: 이력서 프로젝트 설명 수정",
        "6일차: 예상 질문에 STAR 형식으로 답변",
        "7일차: 모의 면접과 누락 근거 최종 점검",
      ],
    },
    relatedSkillGuidance,
    metadata: {
      schemaVersion: "1.0.0",
      modelVersion: "local-keyword-analyzer",
      scoringVersion: "local-1.0.0",
      retrievalUsed: false,
      persisted: false,
    },
  };
}

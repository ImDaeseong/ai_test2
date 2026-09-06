import { describe, expect, it } from "vitest";
import { careerDiffAnalysisResultSchema } from "@/core/schemas/analysisResult";
import { jobReadinessFixtures } from "./jobReadiness.fixtures";
import { buildLocalAnalysis, inspectJobDescription } from "./LocalAnalysisProvider";

function classify(description: string): "ready" | "no-known-skills" | "too-short" {
  const readiness = inspectJobDescription(description);
  if (readiness.ready) return "ready";
  return readiness.reason ?? "no-known-skills";
}

describe("inspectJobDescription semantic regression (labeled fixtures)", () => {
  it.each(jobReadinessFixtures)("classifies '$label' as $expected", ({ description, expected }) => {
    expect(classify(description)).toBe(expected);
  });
});

describe("inspectJobDescription", () => {
  it("is ready only when a known skill is present", () => {
    expect(inspectJobDescription("Python과 AWS로 백엔드 서비스를 운영할 개발자를 찾습니다.").ready).toBe(true);
    const noSkill = inspectJobDescription("매장 운영과 고객 응대를 담당할 매니저를 모집합니다. 경력 3년 이상.");
    expect(noSkill.ready).toBe(false);
    expect(noSkill.reason).toBe("no-known-skills");
  });

  it("is not ready for text below the analyzable length", () => {
    const short = inspectJobDescription("개발자 모집");
    expect(short.ready).toBe(false);
    expect(short.reason).toBe("too-short");
  });

  it("recognizes skills added from real postings (C++/Flutter/HTML)", () => {
    const result = inspectJobDescription("프런트엔드 개발자 모집. 담당업무는 Flutter, HTML, CSS와 C++ 기반 개발입니다.");
    expect(result.ready).toBe(true);
    expect(result.detectedSkills).toEqual(expect.arrayContaining(["Flutter", "HTML", "CSS", "C++"]));
  });

  it("recognizes hardware/CAD skills added from a real 로봇제어 posting", () => {
    const result = inspectJobDescription(
      "로봇제어/강화학습 연구·개발자 채용. 스킬: C, C++, Linux, CATIA, NX, OrCAD, CUDA, MCU, Embedded, SIMD",
    );
    expect(result.ready).toBe(true);
    expect(result.detectedSkills).toEqual(
      expect.arrayContaining(["C++", "Linux", "CATIA", "OrCAD", "CUDA", "MCU", "Embedded", "SIMD"]),
    );
  });

  it("recognizes WPF from a real 'C# WPF 개발자' posting", () => {
    const result = inspectJobDescription("모집분야: C# WPF 개발자. 스킬: C#, WPF, CIM, HCM");
    expect(result.ready).toBe(true);
    expect(result.detectedSkills).toEqual(expect.arrayContaining(["C#", "WPF"]));
  });

  it("does not match the HTML alias inside an unrelated word like 'Dhtml'", () => {
    const result = inspectJobDescription("자사몰 개발자 채용. 스킬: CSS3, Git, HTML5, JavaScript, Node.js, React");
    // A candidate profile whose only "html"-adjacent token is the legacy
    // "Dhtml" (1990s DHTML) must not be reported as having HTML evidence.
    expect(result.detectedSkills).toContain("HTML");
    expect(inspectJobDescription("VC++, Dhtml, Xml 기반 개발 경험이 있습니다.").detectedSkills).not.toContain("HTML");
  });
});

describe("buildLocalAnalysis", () => {
  it("changes requirements and score when the posting changes", () => {
    const candidateProfile = JSON.stringify({
      skills: ["Python", "FastAPI", "PostgreSQL"],
      project: "FastAPI와 PostgreSQL로 API를 구현했습니다.",
    });
    const backend = buildLocalAnalysis({
      jobDescription: "Python FastAPI PostgreSQL 백엔드 개발자를 채용합니다.",
      candidateProfile,
    });
    const ai = buildLocalAnalysis({
      jobDescription: "PyTorch LangChain RAG Vector DB 기반 AI 엔지니어를 채용합니다.",
      candidateProfile,
    });

    expect(backend.jobRequirements.requiredSkills.map((item) => item.label)).toContain("FastAPI");
    expect(ai.jobRequirements.requiredSkills.map((item) => item.label)).toContain("PyTorch");
    expect(backend.fitScore.total).not.toBe(ai.fitScore.total);
    expect(backend.summary).not.toBe(ai.summary);
  });

  it("always returns the application result schema and exactly three projects", () => {
    const result = buildLocalAnalysis({
      jobDescription: "Docker Kubernetes AWS 운영 경험이 있는 개발자를 찾습니다.",
      candidateProfile: "Docker로 서비스를 실행한 경험이 있습니다.".repeat(2),
    });

    expect(() => careerDiffAnalysisResultSchema.parse(result)).not.toThrow();
    expect(result.miniProjects).toHaveLength(3);
  });

  it("shows no gaps anywhere for a full match, instead of inventing fallback categories", () => {
    // Real-data regression: a posting requiring only "Java" against a
    // candidate who has it was a 100% match (missing: 0), yet
    // relatedSkillGuidance/miniProjects/resumeSuggestions/interviewPrep all
    // still showed generic FALLBACK_GAPS content as if something were
    // missing — the no-signal fallback was firing on missing.length === 0
    // without checking whether any requirement was even detected.
    const result = buildLocalAnalysis({
      jobDescription: "Java 백엔드 개발자를 채용합니다.",
      candidateProfile: "Java로 대규모 백엔드 시스템을 설계하고 운영한 경험이 있습니다.".repeat(2),
    });

    expect(result.matches.missing).toHaveLength(0);
    expect(result.jobRequirements.requiredSkills.length).toBeGreaterThan(0);
    expect(result.relatedSkillGuidance).toEqual([]);
    expect(result.resumeSuggestions.skillPriority).toEqual([]);
    expect(result.interviewPrep.weakAreas).toEqual([]);
    // Mini projects still total exactly three (product requirement), but
    // must reference the candidate's own matched skill, not a fake gap.
    expect(result.miniProjects).toHaveLength(3);
    for (const project of result.miniProjects) {
      expect(project.targetGaps).toEqual(["Java"]);
      expect(project.goal).not.toContain("구현 근거를 만듭니다");
    }
  });

  it("still fills relatedSkillGuidance from the FALLBACK_GAPS labels when the posting has zero recognized skills", () => {
    const result = buildLocalAnalysis({
      jobDescription: "매장 운영과 고객 응대를 담당할 매니저를 모집합니다. 성실하고 책임감 있는 분 우대합니다.",
      candidateProfile: "VC++로 PC방 관리프로그램을 개발한 경험이 있습니다. Android, C#, Python도 다룹니다.".repeat(2),
    });

    expect(result.jobRequirements.requiredSkills).toHaveLength(0);
    expect(result.relatedSkillGuidance.length).toBeGreaterThan(0);
    expect(result.relatedSkillGuidance).toEqual(
      result.resumeSuggestions.skillPriority.map((label) =>
        expect.objectContaining({ skill: label, relatedSkills: [] }),
      ),
    );
  });

  it("extracts simulation and physical AI skills from detailed postings", () => {
    const result = buildLocalAnalysis({
      jobDescription: "Unreal Engine, WebGPU, 디지털 트윈, 강화학습, VLA, Sim2Real 경험이 필요합니다.",
      candidateProfile: "Unity와 WebGL 기반 시뮬레이션 프로젝트를 개발했습니다.",
    });

    const labels = result.jobRequirements.requiredSkills.map((item) => item.label);
    expect(labels).toEqual(expect.arrayContaining([
      "Unreal Engine",
      "WebGPU",
      "VLA",
      "Reinforcement Learning",
      "Sim2Real",
      "Digital Twin",
    ]));
  });

  it("explains a missing skill's ontology relation when the candidate has no bridge skill", () => {
    const result = buildLocalAnalysis({
      jobDescription: "RAG 기반 검색 시스템을 구축할 AI 엔지니어를 찾습니다.",
      candidateProfile: "Python으로 데이터 파이프라인을 구축한 경험이 있습니다.",
    });

    expect(result.relatedSkillGuidance).toEqual([
      expect.objectContaining({
        skill: "RAG",
        relatedSkills: ["Vector DB", "LangChain", "LLM"],
      }),
    ]);
    expect(result.relatedSkillGuidance[0].reason).not.toContain("이미");
  });

  it("still gives guidance for a missing skill with no taxonomy relation, instead of omitting it", () => {
    const result = buildLocalAnalysis({
      jobDescription: "Python 기반 데이터 엔지니어를 찾습니다.",
      candidateProfile: "자바스크립트와 웹 서비스를 개발한 경험이 있습니다.".repeat(2),
    });

    const pythonGuidance = result.relatedSkillGuidance.find((guidance) => guidance.skill === "Python");
    expect(pythonGuidance).toBeDefined();
    expect(pythonGuidance?.relatedSkills).toEqual([]);
    expect(pythonGuidance?.reason).toContain("Python");
  });

  it("names the candidate's existing skill as a bridge toward a missing related skill", () => {
    const result = buildLocalAnalysis({
      jobDescription: "Docker Kubernetes 운영 경험이 있는 개발자를 찾습니다.",
      candidateProfile: "Docker로 서비스를 컨테이너화해 운영한 경험이 있습니다.".repeat(2),
    });

    const kubernetesGuidance = result.relatedSkillGuidance.find((guidance) => guidance.skill === "Kubernetes");
    expect(kubernetesGuidance?.reason).toContain("Docker");
    expect(kubernetesGuidance?.reason).toContain("이미");
  });

  it("covers ontology relations added for web/data/delivery skills", () => {
    const result = buildLocalAnalysis({
      jobDescription: "Next.js, PostgreSQL, GitHub Actions, Airflow, WPF 경험이 있는 개발자를 찾습니다.",
      candidateProfile: "React와 SQL 기반 웹 서비스를 개발한 경험이 있습니다.",
    });

    const bySkill = Object.fromEntries(result.relatedSkillGuidance.map((g) => [g.skill, g]));
    expect(bySkill["Next.js"].relatedSkills).toEqual(["React"]);
    expect(bySkill["PostgreSQL"].relatedSkills).toEqual(["SQL"]);
    expect(bySkill["GitHub Actions"].relatedSkills).toEqual(["CI/CD"]);
    expect(bySkill["Airflow"].relatedSkills).toEqual(["Spark", "Python"]);
    expect(bySkill["WPF"].relatedSkills).toEqual(["C#"]);
  });

  it("covers ontology relations added for base-language and successor-API links", () => {
    const result = buildLocalAnalysis({
      jobDescription:
        "FastAPI, Django, Flask, Spring, Kotlin, PyTorch, TensorFlow, WebGPU 경험이 있는 개발자를 찾습니다.",
      candidateProfile: "웹 서비스와 백엔드 시스템을 개발한 경험이 있습니다.".repeat(2),
    });

    const bySkill = Object.fromEntries(result.relatedSkillGuidance.map((g) => [g.skill, g]));
    expect(bySkill["FastAPI"].relatedSkills).toEqual(["Python"]);
    expect(bySkill["Django"].relatedSkills).toEqual(["Python"]);
    expect(bySkill["Flask"].relatedSkills).toEqual(["Python"]);
    expect(bySkill["Spring"].relatedSkills).toEqual(["Java"]);
    expect(bySkill["Kotlin"].relatedSkills).toEqual(["Java"]);
    expect(bySkill["PyTorch"].relatedSkills).toEqual(["CUDA", "Python"]);
    expect(bySkill["TensorFlow"].relatedSkills).toEqual(["CUDA", "Python"]);
    expect(bySkill["WebGPU"].relatedSkills).toEqual(["WebGL"]);
  });

  it("names Python as the bridge skill for a missing Python web framework", () => {
    const result = buildLocalAnalysis({
      jobDescription: "Django 기반 백엔드 개발자를 채용합니다.",
      candidateProfile: "Python으로 데이터 처리 스크립트를 여러 개 작성한 경험이 있습니다.".repeat(2),
    });

    const djangoGuidance = result.relatedSkillGuidance.find((guidance) => guidance.skill === "Django");
    expect(djangoGuidance?.reason).toContain("Python");
    expect(djangoGuidance?.reason).toContain("이미");
  });

  it("covers ontology relations added in the second pass (frontend runtime links, engine languages, new DB/language skills)", () => {
    const result = buildLocalAnalysis({
      jobDescription:
        "TypeScript, Node.js, React, Vue.js, Angular, Unity, Unreal Engine, BeautifulSoup, MSSQL, MariaDB, Delphi 경험이 있는 개발자를 찾습니다.",
      candidateProfile: "웹 서비스와 게임 클라이언트를 개발한 경험이 있습니다.".repeat(2),
    });

    const bySkill = Object.fromEntries(result.relatedSkillGuidance.map((g) => [g.skill, g]));
    expect(bySkill["TypeScript"].relatedSkills).toEqual(["JavaScript"]);
    expect(bySkill["Node.js"].relatedSkills).toEqual(["JavaScript"]);
    expect(bySkill["React"].relatedSkills).toEqual(["JavaScript"]);
    expect(bySkill["Vue.js"].relatedSkills).toEqual(["JavaScript"]);
    expect(bySkill["Angular"].relatedSkills).toEqual(["TypeScript"]);
    expect(bySkill["Unity"].relatedSkills).toEqual(["C#"]);
    expect(bySkill["Unreal Engine"].relatedSkills).toEqual(["C++"]);
    expect(bySkill["BeautifulSoup"].relatedSkills).toEqual(["Python"]);
    expect(bySkill["MS SQL Server"].relatedSkills).toEqual(["SQL"]);
    expect(bySkill["MariaDB"].relatedSkills).toEqual(["SQL"]);
    // Delphi has no relatedTo — it still gets a direct-learning guidance
    // entry (empty relatedSkills) instead of being silently omitted.
    expect(bySkill["Delphi"].relatedSkills).toEqual([]);
    expect(bySkill["Delphi"].reason).toContain("Delphi");

    const requiredLabels = result.jobRequirements.requiredSkills.map((item) => item.label);
    expect(requiredLabels).toEqual(expect.arrayContaining(["Delphi", "MS SQL Server"]));
  });

  it("recognizes Delphi and MS SQL Server from a real 'C, C#, C++, Delphi, JAVA, MSSQL, DBMS' posting", () => {
    const result = inspectJobDescription(
      "채용분야: 관제/정산시스템 개발자. 스킬: C, C#, C++, Delphi, JAVA, MSSQL, DBMS",
    );
    expect(result.ready).toBe(true);
    expect(result.detectedSkills).toEqual(
      expect.arrayContaining(["C#", "C++", "Delphi", "Java", "MS SQL Server"]),
    );
  });

  it("bridges a missing skill through a multi-hop relatedTo chain when no direct neighbor matches", () => {
    // LangGraph -> LangChain -> LLM -> OpenAI is a 3-hop relatedTo chain.
    // The candidate only has OpenAI, two hops past LangGraph's direct
    // neighbor (LangChain), so a 1-hop lookup would find no bridge at all.
    const result = buildLocalAnalysis({
      jobDescription: "LangGraph 기반 에이전트 시스템을 구축할 AI 엔지니어를 찾습니다.",
      candidateProfile: "OpenAI API로 챗봇을 만든 경험이 있습니다.".repeat(2),
    });

    const langGraphGuidance = result.relatedSkillGuidance.find((guidance) => guidance.skill === "LangGraph");
    expect(langGraphGuidance?.relatedSkills).toEqual(["LangChain"]);
    expect(langGraphGuidance?.reason).toContain("OpenAI → LLM → LangChain");
  });

  it("reports HTML as missing, not a strong match, for a candidate whose only evidence is legacy 'Dhtml'", () => {
    const result = buildLocalAnalysis({
      jobDescription: "CSS3, HTML5, JavaScript 기반 프런트엔드 개발자를 찾습니다.",
      candidateProfile: "VC++(MFC, ATL, OCX), Dhtml, Xml 기반 시스템을 개발한 경험이 있습니다.".repeat(2),
    });

    expect(result.matches.strong.map((match) => match.requirement)).not.toContain("HTML");
    expect(result.matches.missing.map((match) => match.requirement)).toContain("HTML");
  });

  it("does not bridge a missing skill beyond MAX_BRIDGE_DEPTH hops", () => {
    // VLA -> Reinforcement Learning -> Sim2Real -> Digital Twin -> Unreal
    // Engine/Unity is 4 hops from VLA's direct neighbor (Reinforcement
    // Learning), past the 3-hop bridge limit, so no bridge should be found.
    const result = buildLocalAnalysis({
      jobDescription: "VLA 모델을 다루는 로보틱스 엔지니어를 찾습니다.",
      candidateProfile: "Unity로 3D 시뮬레이션 환경을 개발한 경험이 있습니다.".repeat(2),
    });

    const vlaGuidance = result.relatedSkillGuidance.find((guidance) => guidance.skill === "VLA");
    expect(vlaGuidance?.reason).not.toContain("이미");
    expect(vlaGuidance?.reason).not.toContain("→");
  });
});

describe("jobRequirements.domain (경력/학력/우대조건 extraction)", () => {
  // Real-data regression: a 다이캐스팅 품질 팀장 posting (no SKILLS-taxonomy
  // keyword anywhere in the text) against a software-dev candidate produced
  // an entirely empty jobRequirements — the actual 경력/학력/우대조건 the
  // posting stated were silently dropped, and the UI's "도메인" panel showed
  // "추출된 항목이 없습니다." even though that information was in the text.
  // domain must reflect the posting regardless of candidate fit or SKILLS
  // coverage, since this tool isn't only for a single candidate's résumé.
  it("extracts career/education/preferred conditions from a posting with zero recognized tech skills", () => {
    const jobDescription =
      "다이캐스팅 품질 팀장급 모집-베트남주재원\n상세요강\n모집요강\n모집분야\n품질보증 팀장급 모집-베트남주재원\n" +
      "모집인원\n1명\n고용형태\n정규직(수습 3개월)\n지원자격\n경력\n경력\n(5년이상)\n학력\n학력무관\n" +
      "우대조건\n기본우대\n해외근무 가능자, 유관업무 경력자(5년)";

    const result = buildLocalAnalysis({
      jobDescription,
      candidateProfile: "VC++로 PC방 관리프로그램을 개발한 경험이 있습니다. Android, C#, Python도 다룹니다.".repeat(2),
    });

    expect(result.jobRequirements.requiredSkills).toHaveLength(0);
    const labels = result.jobRequirements.domain.map((item) => item.label);
    expect(labels).toContain("경력 5년이상");
    expect(labels).toContain("학력 학력무관");
    expect(labels).toContain("해외근무 가능자");
    expect(labels).toContain("유관업무 경력자(5년)");
  });

  it("also extracts domain requirements when the posting has recognized tech skills", () => {
    const jobDescription = "지원자격\n경력\n경력\n(7년이상)\n학력\n학력무관\n스킬\nOracle, PL/SQL, PostgreSQL, Python";
    const result = buildLocalAnalysis({
      jobDescription,
      candidateProfile: "Python과 PostgreSQL로 백엔드를 개발한 경험이 있습니다.",
    });

    expect(result.jobRequirements.requiredSkills.length).toBeGreaterThan(0);
    expect(result.jobRequirements.domain.map((item) => item.label)).toEqual(
      expect.arrayContaining(["경력 7년이상", "학력 학력무관"]),
    );
  });

  it("recognizes the 신입·경력 career label", () => {
    const jobDescription = "지원자격\n경력\n신입·경력\n학력\n(직무별 상이 / 상세요강 참조)";
    const result = buildLocalAnalysis({ jobDescription, candidateProfile: "경력 사항입니다." });

    expect(result.jobRequirements.domain.map((item) => item.label)).toContain("신입·경력");
  });

  // Real-data regression: a broader audit of every stored data/*.json case
  // found 9 postings where domain came back empty despite having a
  // 지원자격 section — a second jobkorea layout puts the career value inline
  // ("경력\n경력(10년이상)", no newline before the parenthesis) instead of on
  // its own line, and "경력무관" (career not required) has no parentheses at
  // all. Both were silently dropped by the first regex.
  it("recognizes the inline mobile-layout career value with no newline before the parenthesis", () => {
    const jobDescription = "지원자격\n경력\n경력(10년이상)\n\n접수기간/방법\n...";
    const result = buildLocalAnalysis({ jobDescription, candidateProfile: "경력 사항입니다." });

    expect(result.jobRequirements.domain.map((item) => item.label)).toContain("경력 10년이상");
  });

  it("recognizes the 경력무관 career label", () => {
    const jobDescription = "지원자격\n경력\n경력무관\n\n스킬\n\n역량\n성실성";
    const result = buildLocalAnalysis({ jobDescription, candidateProfile: "경력 사항입니다." });

    expect(result.jobRequirements.domain.map((item) => item.label)).toContain("경력무관");
  });

  // Real-data regression: a full-dataset audit found 10/161 postings put a
  // parenthesized qualifier ("(졸업예정자 가능)") on its own line after the 학력
  // value instead of on the same line — it was silently dropped.
  it("folds a parenthesized 학력 qualifier on the following line back into the value", () => {
    const jobDescription = "지원자격\n경력\n경력\n(5년이상)\n학력\n대졸이상\n(졸업예정자 가능)\n스킬\nJava";
    const result = buildLocalAnalysis({ jobDescription, candidateProfile: "경력 사항입니다." });

    expect(result.jobRequirements.domain.map((item) => item.label)).toContain("학력 대졸이상 (졸업예정자 가능)");
  });

  it("returns no domain items when the posting has no 지원자격 section", () => {
    const result = buildLocalAnalysis({
      jobDescription: "회사 소개와 복리후생 안내만 있는 채용공고입니다.".repeat(3),
      candidateProfile: "후보자 프로필입니다.",
    });

    expect(result.jobRequirements.domain).toEqual([]);
  });

  // Real-data regression: a stored posting's free-text title ended in
  // "...보험 경험 우대\n⭐ 158명 이상 찜한 기업" — that sentence-ending "우대"
  // satisfied the old regex before the real "우대조건" heading further down
  // was ever reached, so the extracted "preferred" item was the company
  // interest banner instead of the posting's actual preferred conditions.
  it("skips a sentence-ending '우대' in the posting title and extracts the real 우대조건 heading", () => {
    const jobDescription =
      "웹프로그래머 프리랜서 개발자(경력직)-React, 은행, 보험 경험 우대\n⭐ 158명 이상 찜한 기업\n" +
      "지원자격\n경력\n경력\n(6년이상)\n학력\n고졸이상\n스킬\nJAVA, React, Spring, Vue.js\n" +
      "우대조건\n기본우대\n정보처리기사, 정보처리산업기사";

    const result = buildLocalAnalysis({ jobDescription, candidateProfile: "경력 사항입니다." });

    const labels = result.jobRequirements.domain.map((item) => item.label);
    expect(labels).not.toContain("⭐ 158명 이상 찜한 기업");
    expect(labels).toContain("정보처리기사");
    expect(labels).toContain("정보처리산업기사");
  });
});

/**
 * Labeled, PII-free job-description fixtures for inspectJobDescription.
 *
 * The real saved postings in `data/*.json` carry personal data and are
 * git-ignored, so they cannot back a committed regression test. These synthetic
 * postings mirror the same patterns (analyzable dev roles vs. non-technical
 * summaries vs. too-short) and give the readiness classifier a permanent,
 * shareable semantic guard. Add a case here whenever a real posting is
 * misclassified, reproduced as a PII-free equivalent.
 */
export type JobReadinessFixture = {
  label: string;
  description: string;
  expected: "ready" | "no-known-skills" | "too-short";
};

export const jobReadinessFixtures: JobReadinessFixture[] = [
  {
    label: "backend role names known skills",
    description:
      "백엔드 개발자를 모집합니다. 담당업무: Python과 Django로 API를 개발하고 PostgreSQL, AWS로 운영합니다. 자격요건: Docker, Kubernetes 경험.",
    expected: "ready",
  },
  {
    label: "frontend role with recently added skills",
    description: "프런트엔드 개발자 채용. 담당업무: Flutter, HTML, CSS와 TypeScript로 앱과 웹을 개발합니다.",
    expected: "ready",
  },
  {
    label: "devops role",
    description: "DevOps 엔지니어 모집. CI/CD 파이프라인을 구축하고 Kubernetes, Terraform으로 인프라를 운영합니다.",
    expected: "ready",
  },
  {
    label: "strategy CTO summary, no concrete tech",
    description:
      "자동차 대여 산업 플랫폼 개발 CTO 모집. 모집분야 전략수립 및 연구개발 총괄. 고용형태 정규직. 급여 회사 내규에 따름. 근무지 서울. 지원자격 경력 10년이상 학력 대졸이상.",
    expected: "no-known-skills",
  },
  {
    label: "non-technical manager role",
    description:
      "매장 운영과 고객 응대를 담당할 매니저를 모집합니다. 자격요건: 관련 경력 3년 이상. 우대사항: 리더십과 커뮤니케이션 능력이 뛰어난 분.",
    expected: "no-known-skills",
  },
  {
    label: "site summary boilerplate with a requirements heading but no skill",
    description:
      "채용공고 회사소개 상세요강 접수기간 기업정보 추천공고 모집요강 모집분야 개발 담당자 모집인원 1명 고용형태 정규직 급여 회사 내규 복리후생 성과급 지원자 현황 로그인 기업구분 벤처기업.",
    expected: "no-known-skills",
  },
  {
    label: "robotics role names robot/mechatronics/embedded skills",
    description:
      "로봇 시뮬레이션 총괄 CTO 모집. 담당업무: 메카트로닉스와 임베디드 펌웨어, 자율주행 알고리즘을 설계합니다.",
    expected: "ready",
  },
  {
    label: "too short to analyze",
    description: "개발자 모집",
    expected: "too-short",
  },
];

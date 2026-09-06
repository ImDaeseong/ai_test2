import { describe, expect, it } from "vitest";
import {
  hasSufficientJobDetail,
  JobImportError,
  parseJobKoreaDetailHtml,
  parseJobKoreaHtml,
  validateJobKoreaUrl,
} from "./jobKoreaImporter";

describe("validateJobKoreaUrl", () => {
  it("accepts only JobKorea detail URLs", () => {
    expect(validateJobKoreaUrl("https://www.jobkorea.co.kr/Recruit/GI_Read/49431616").hostname).toBe("www.jobkorea.co.kr");
    expect(() => validateJobKoreaUrl("http://www.jobkorea.co.kr/Recruit/GI_Read/1")).toThrow(JobImportError);
    expect(() => validateJobKoreaUrl("https://evil.example/Recruit/GI_Read/1")).toThrow(JobImportError);
    expect(() => validateJobKoreaUrl("https://www.jobkorea.co.kr/Recruit")).toThrow(JobImportError);
  });
});

describe("parseJobKoreaHtml", () => {
  it("returns structured JSON from a public posting page", () => {
    const html = `<html><head>
      <meta property="og:title" content="테스트회사 채용 - AI 백엔드 개발자 | 잡코리아">
      </head><body><main>
      <h1>AI 백엔드 개발자</h1>
      <section><h2>모집요강</h2><p>FastAPI와 Python을 사용한 API 개발</p></section>
      <section><h2>지원자격</h2><p>백엔드 개발 경력 및 RAG 서비스 경험을 우대합니다.</p></section>
      <section><h2>접수기간/방법</h2><p>잡코리아 즉시지원으로 접수합니다.</p></section>
      </main></body></html>`;
    expect(parseJobKoreaHtml(html, "https://www.jobkorea.co.kr/Recruit/GI_Read/1", "2026-07-31T00:00:00.000Z")).toEqual({
      source: "jobkorea",
      sourceUrl: "https://www.jobkorea.co.kr/Recruit/GI_Read/1",
      title: "테스트회사 채용 - AI 백엔드 개발자",
      company: "테스트회사",
      description: expect.stringContaining("FastAPI와 Python"),
      fetchedAt: "2026-07-31T00:00:00.000Z",
      sufficient: true,
    });
  });

  it("removes numeric-only internal skill codes", () => {
    const html = `<html><head><title>테스트회사 채용 - 개발자 | 잡코리아</title></head><body><main>
      <h1>개발자</h1><p>1710001335</p><p>Python 개발 업무를 담당합니다.</p>
      <p>지원 자격과 업무 내용을 충분히 설명하기 위한 공개 채용공고 본문입니다.</p>
      <p>서비스 설계, 구현, 테스트, 배포 및 운영 과정에 참여하고 동료와 기술 내용을 공유합니다.</p>
    </main></body></html>`;

    const result = parseJobKoreaHtml(html, "https://www.jobkorea.co.kr/Recruit/GI_Read/1");
    expect(result.description).toContain("Python 개발 업무");
    expect(result.description).not.toContain("1710001335");
  });
});

describe("hasSufficientJobDetail", () => {
  it("treats JobKorea summary boilerplate as insufficient", () => {
    // A real captured summary: company meta + how-to-apply, no requirements.
    const summaryOnly =
      "채용공고 ㈜닷밀 본부장 채용 D-37 경력 상세요강 기업 정보 모집분야 본부장 급여 회사 내규에 따름 " +
      "근무지 서울 마포구 지도 지원자격 경력 경력(8년이상) 접수기간/방법 방법 잡코리아 즉시지원 " +
      "지원자 현황 로그인 하고 지원자 현황을 확인해보세요! 기업구분 벤처기업 " +
      "해당공고 불법·허위·과장 또는 오류 신고하기 본 채용정보는 해당 기업이 자율적으로 등록한 것으로, " +
      "잡코리아는 게재된 채용정보의 정확성이나 적법성을 보장하지 않습니다.";
    expect(hasSufficientJobDetail(summaryOnly)).toBe(false);
  });

  it("treats a description that names known skills as sufficient", () => {
    const withDetail =
      "담당업무: FastAPI와 Python으로 백엔드 API를 설계하고 구현합니다. " +
      "자격요건: 백엔드 개발 경력 3년 이상. 우대사항: RAG 서비스 경험.";
    expect(hasSufficientJobDetail(withDetail)).toBe(true);
  });

  it("is insufficient when a requirements section names no analyzer-known skill", () => {
    // Requirement markers used to force success on their own; a JD the local
    // analyzer cannot extract skills from must now be insufficient so the user
    // is asked to paste more, not shown an empty analysis.
    const requirementsNoSkill =
      "담당업무: 매장 운영과 고객 응대를 담당합니다. 자격요건: 관련 경력 3년 이상. " +
      "우대사항: 리더십과 커뮤니케이션 능력이 뛰어난 분.";
    expect(hasSufficientJobDetail(requirementsNoSkill)).toBe(false);
  });

  it("flags a non-tech summary with no recognizable skills as insufficient", () => {
    // A JobKorea summary format that carries none of the old summary markers,
    // no requirement section, and no skill keyword — this used to slip through
    // as sufficient and produce a silently empty analysis.
    const nonTechSummary =
      "자동차 대여 산업 플랫폼 개발 CTO 모집 상세요강 접수기간 방법 기업정보 추천공고 " +
      "채용정보에 잘못된 내용이 있을 경우 문의해주세요. 모집요강 모집분야 전략수립 및 연구개발 총괄 " +
      "모집인원 1명 고용형태 정규직 급여 회사 내규에 따름 근무시간 주5일 근무지주소 서울 송파구 " +
      "지원자격 경력 10년이상 학력 대졸이상";
    expect(hasSufficientJobDetail(nonTechSummary)).toBe(false);
  });

  it("treats a summary that still names a known skill as sufficient", () => {
    const withSkill = "백엔드 개발자 모집. 접수기간 방법 기업정보. Python과 AWS 경험 필요.";
    expect(hasSufficientJobDetail(withSkill)).toBe(true);
  });
});

describe("parseJobKoreaDetailHtml", () => {
  it("decodes the serialized detail content from the Next.js payload", () => {
    const html = String.raw`<html><body><script>self.__next_f.push([1,"payload:
      \u003cdiv id=\"template_common_title\"\u003e
      \u003ch1\u003ePhysical AI 로봇 시뮬레이션 기술총괄\u003c/h1\u003e
      \u003cp\u003eWebGPU와 디지털 트윈 기반 Sim2Real 파이프라인을 설계합니다.\u003c/p\u003e
      \u003cp\u003e강화학습 및 VLA 경험을 우대합니다.\u003c/p\u003e
      \u003c/div\u003e"])</script></body></html>`;

    const result = parseJobKoreaDetailHtml(html);
    expect(result).toContain("Physical AI 로봇 시뮬레이션 기술총괄");
    expect(result).toContain("WebGPU와 디지털 트윈");
    expect(result).not.toContain("self.__next_f");
  });
});

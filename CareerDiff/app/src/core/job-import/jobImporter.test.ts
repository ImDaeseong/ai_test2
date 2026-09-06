import { describe, expect, it } from "vitest";
import { JobImportError, parseGenericPosting, validateJobUrl } from "./jobImporter";

describe("validateJobUrl", () => {
  it("accepts detail URLs from each supported site", () => {
    expect(validateJobUrl("https://www.jobkorea.co.kr/Recruit/GI_Read/49722051").site.source).toBe("jobkorea");
    expect(validateJobUrl("https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=54596713").site.source).toBe(
      "saramin",
    );
    expect(validateJobUrl("https://www.incruit.com/jobdb_info/jobpost.asp?job=2607290003704").site.source).toBe(
      "incruit",
    );
    // Incruit listing links use www but 301 to job.incruit.com; both are valid.
    expect(validateJobUrl("https://job.incruit.com/jobdb_info/jobpost.asp?job=1").site.source).toBe("incruit");
  });

  it("keeps query parameters and matching is case-insensitive on host", () => {
    const { url } = validateJobUrl("https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=1&view_type=list");
    expect(url.searchParams.get("rec_idx")).toBe("1");
  });

  it("rejects non-https, unknown hosts, and non-detail paths", () => {
    expect(() => validateJobUrl("http://www.jobkorea.co.kr/Recruit/GI_Read/1")).toThrow(JobImportError);
    expect(() => validateJobUrl("https://evil.example/zf_user/jobs/relay/view?rec_idx=1")).toThrow(JobImportError);
    expect(() => validateJobUrl("https://www.saramin.co.kr/zf_user/jobs/relay/view")).toThrow(JobImportError);
    expect(() => validateJobUrl("https://www.incruit.com/jobdb_info/jobpost.asp")).toThrow(JobImportError);
    expect(() => validateJobUrl("https://www.jobkorea.co.kr/Recruit")).toThrow(JobImportError);
  });
});

describe("parseGenericPosting", () => {
  it("builds a posting and flags a summary-only body as insufficient", () => {
    const html = `<html><head><meta property="og:title" content="사람인 - 백엔드 채용"></head><body><main>
      회사 소개와 복리후생 안내입니다. 성과급과 간식을 제공하며 유연근무제를 시행합니다.
      지원자 현황 로그인 하고 지원자 현황을 확인해보세요. 기업구분 중소기업이며 설립 10년차입니다.
      해당공고 불법·허위·과장 또는 오류 신고하기. 본 채용정보의 정확성은 보장하지 않습니다.
    </main></body></html>`;
    const posting = parseGenericPosting(html, "saramin", "https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=1");
    expect(posting.source).toBe("saramin");
    expect(posting.title).toContain("백엔드 채용");
    expect(posting.sufficient).toBe(false);
  });

  it("flags a body with real requirement sections as sufficient", () => {
    const html = `<html><head><title>인크루트 개발자</title></head><body><main>
      담당업무: FastAPI로 백엔드 API를 설계하고 구현하며 서비스 배포와 운영을 담당합니다.
      자격요건: 백엔드 개발 경력 3년 이상. 우대사항: 클라우드 환경 운영 경험이 있는 분.
    </main></body></html>`;
    const posting = parseGenericPosting(html, "incruit", "https://www.incruit.com/jobdb_info/jobpost.asp?job=1");
    expect(posting.sufficient).toBe(true);
  });
});

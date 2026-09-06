import { expect, test } from "@playwright/test";

const JOB_DESCRIPTION =
  "우리는 TypeScript와 Node.js로 백엔드 서비스를 구축할 백엔드 엔지니어를 찾고 있습니다. PostgreSQL과 AWS 경험이 필요합니다.";
const CANDIDATE_PROFILE =
  "2년간 TypeScript와 Node.js로 백엔드 서비스를 운영했습니다. PostgreSQL 기반 리포팅 서비스의 스키마를 설계했습니다.";

test.describe("CareerDiff analyzer flow", () => {
  test("shows the privacy notice and per-field sensitive-data warning before any input", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("브라우저와 CareerDiff/data 폴더에 저장됩니다")).toBeVisible();
    await expect(page.getByText("민감한 정보는 첨부하지 마세요")).toBeVisible();
  });

  test("enables analyze once both fields are long enough (docs/PRODUCT.md)", async ({ page }) => {
    await page.goto("/");
    const analyzeButton = page.getByRole("button", { name: "분석하기" });
    await expect(analyzeButton).toBeDisabled();
    // A disabled button must say why, never read as an unexplained no-op.
    await expect(page.getByText("분석하려면 채용공고와 이력서/커리어를 30자 이상 입력하세요.")).toBeVisible();

    await page.getByLabel("채용공고", { exact: true }).fill("short");
    await expect(analyzeButton).toBeDisabled();

    await page.getByLabel("채용공고", { exact: true }).fill(JOB_DESCRIPTION);
    await expect(analyzeButton).toBeDisabled();
    await expect(page.getByText("분석하려면 이력서/커리어를 30자 이상 입력하세요.")).toBeVisible();

    await page.getByLabel("이력서 / 커리어 / 프로젝트").fill(CANDIDATE_PROFILE);
    await expect(analyzeButton).toBeEnabled();
    await expect(page.getByText(/30자 이상 입력하세요/)).toHaveCount(0);
  });

  test("stays analyzable with a non-blocking warning when no skill is recognized", async ({ page }) => {
    await page.goto("/");
    const analyzeButton = page.getByRole("button", { name: "분석하기" });

    // A long job with no analyzer-known skill plus a valid resume: the local
    // dictionary is incomplete, so the button must NOT be blocked — it stays
    // enabled and only warns that results may be limited.
    await page
      .getByLabel("채용공고", { exact: true })
      .fill("이 공고는 매장 운영과 고객 응대를 담당할 매니저를 모집합니다. 경력 3년 이상 필요합니다.");
    await page.getByLabel("이력서 / 커리어 / 프로젝트").fill(CANDIDATE_PROFILE);

    await expect(analyzeButton).toBeEnabled();
    await expect(page.getByText(/인식된 기술 요건이 없어/)).toBeVisible();
  });

  test("runs a full analysis and renders all MVP dashboard sections (docs/PRODUCT.md)", async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });

    await page.goto("/");
    await page.getByLabel("채용공고", { exact: true }).fill(JOB_DESCRIPTION);
    await page.getByLabel("이력서 / 커리어 / 프로젝트").fill(CANDIDATE_PROFILE);
    await page.getByRole("button", { name: "분석하기" }).click();

    await expect(page.getByRole("heading", { name: "적합도 점수" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "채용 요건" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "매칭 결과" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "이력서 개선 제안" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "보완 프로젝트 추천" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "면접 준비" })).toBeVisible();

    // docs/PRODUCT.md: exactly 3 mini project recommendations.
    const miniProjectCards = page.locator("article");
    await expect(miniProjectCards).toHaveCount(3);

    expect(consoleErrors).toEqual([]);
  });

  test("shows a validation error for an empty API request without crashing the UI", async ({ page, request }) => {
    const response = await request.post("/api/analyze", { data: { jobDescription: "", candidateProfile: "" } });
    expect(response.status()).toBe(400);
    const body = await response.json();
    expect(body.error.code).toBe("VALIDATION_ERROR");

    // The page itself should still be usable after a failed request path exists.
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "CareerDiff" })).toBeVisible();
  });
});

/** Exercise the live OpenAI analysis path with fixed synthetic data only. */

const baseUrl = process.env.CAREERDIFF_BASE_URL || "http://127.0.0.1:3011";

if (process.env.CAREERDIFF_LIVE_OPENAI !== "1") {
  console.error("HOLD: set CAREERDIFF_LIVE_OPENAI=1 after starting the app with an OpenAI key.");
  process.exit(2);
}

const payload = {
  jobDescription:
    "가상 회사는 Python, FastAPI, PostgreSQL, Docker 경험이 있는 백엔드 개발자를 찾습니다. " +
    "REST API 설계와 자동화 테스트 경험이 필수이며 AWS 경험은 우대합니다. ".repeat(2),
  candidateProfile:
    "가상 후보자는 Python 3년, Flask 2년, PostgreSQL 2년 경험이 있습니다. " +
    "pytest로 단위 테스트를 작성했고 Docker로 개발 환경을 구성했습니다. " +
    "FastAPI와 AWS 실무 경험은 없습니다. ".repeat(2),
  targetRole: "백엔드 개발자",
  targetSeniority: "미드레벨",
  allowExternalProcessing: true,
};

const response = await fetch(`${baseUrl}/api/analyze`, {
  method: "POST",
  headers: { "content-type": "application/json; charset=utf-8" },
  body: JSON.stringify(payload),
  signal: AbortSignal.timeout(150_000),
});

if (!response.ok) {
  console.error(`FAIL: CareerDiff live OpenAI request returned HTTP ${response.status}.`);
  process.exit(1);
}

const body = await response.json();
const result = body.result;
const nonStrongGaps = [...result.matches.weak, ...result.matches.missing, ...result.matches.risks]
  .map((item) => `${item.requirement} ${item.reason}`)
  .join(" ");
const strongRequirements = result.matches.strong.map((item) => item.requirement).join(" ");
const projectGaps = result.miniProjects.flatMap((item) => item.targetGaps).join(" ");

const checks = {
  schemaResultPresent: Boolean(result.summary),
  detectsFastApiGap: /FastAPI/i.test(nonStrongGaps),
  detectsAwsGap: /AWS/i.test(nonStrongGaps),
  doesNotClaimAbsentSkillsAsStrong: !/FastAPI|AWS/i.test(strongRequirements),
  exactlyThreeProjects: result.miniProjects.length === 3,
  projectsMapToBothGaps: /FastAPI/i.test(projectGaps) && /AWS/i.test(projectGaps),
  responseNotPersisted: body.privacy.persisted === false && result.metadata.persisted === false,
  rawInputNotLogged: body.privacy.rawInputLogged === false,
  retrievalDisabled: result.metadata.retrievalUsed === false,
};
const failed = Object.entries(checks).filter(([, passed]) => !passed).map(([name]) => name);
if (failed.length) {
  console.error(`FAIL: CareerDiff live quality checks failed: ${failed.join(", ")}`);
  process.exit(1);
}

console.log(`PASS OPENAI_LIVE model=${process.env.OPENAI_MODEL || "gpt-6-luna"} store=false synthetic_input=true checks=${Object.keys(checks).length}`);

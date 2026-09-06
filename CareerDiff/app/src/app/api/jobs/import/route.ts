import { importJobPosting, JobImportError } from "@/core/job-import/jobImporter";

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: { message: "요청 본문은 JSON이어야 합니다." } }, { status: 400 });
  }
  const url = typeof body === "object" && body !== null && "url" in body ? (body as { url?: unknown }).url : undefined;
  if (typeof url !== "string") {
    return Response.json({ error: { message: "url 문자열을 입력해 주세요." } }, { status: 400 });
  }
  try {
    return Response.json({ job: await importJobPosting(url) });
  } catch (error) {
    if (error instanceof JobImportError) {
      return Response.json({ error: { message: error.message } }, { status: error.status });
    }
    return Response.json(
      { error: { message: "채용공고를 가져오지 못했습니다. 잠시 후 다시 시도해 주세요." } },
      { status: 502 },
    );
  }
}

import { analysisValidationCaseSchema } from "@/core/validation/validationCaseSchema";
import { BodyTooLargeError, readJsonLimited } from "@/core/http/readJsonLimited";
import { listValidationCaseFiles, saveValidationCaseFile } from "@/core/validation/validationCaseFileStore";

export async function GET() {
  try {
    return Response.json({ cases: await listValidationCaseFiles() });
  } catch {
    return Response.json({ error: { message: "검증 데이터를 불러오지 못했습니다." } }, { status: 500 });
  }
}

const MAX_BODY_BYTES = 1_000_000;

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await readJsonLimited(request, MAX_BODY_BYTES);
  } catch (error) {
    if (error instanceof BodyTooLargeError) {
      return Response.json({ error: { message: "요청 본문이 너무 큽니다." } }, { status: 413 });
    }
    return Response.json({ error: { message: "요청 본문은 JSON이어야 합니다." } }, { status: 400 });
  }

  const parsed = analysisValidationCaseSchema.safeParse(body);
  if (!parsed.success) {
    return Response.json({ error: { message: "검증 데이터 형식이 올바르지 않습니다." } }, { status: 400 });
  }

  try {
    return Response.json(await saveValidationCaseFile(parsed.data));
  } catch {
    return Response.json({ error: { message: "검증 JSON 파일을 저장하지 못했습니다." } }, { status: 500 });
  }
}

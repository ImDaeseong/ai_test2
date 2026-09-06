import { inspectJobDescription } from "@/core/analysis/LocalAnalysisProvider";

export type ImportedJobPosting = {
  source: "jobkorea" | "saramin" | "incruit";
  sourceUrl: string;
  title: string;
  company: string;
  description: string;
  fetchedAt: string;
  /**
   * False when the import only captured JobKorea's summary boilerplate
   * (company info, benefits, how-to-apply) without the actual job detail
   * (담당업무/자격요건/우대사항). The UI then asks the user to paste the
   * detail manually. JobKorea now renders that detail client-side, so this
   * is often false — see docs and the manual-paste fallback in the panel.
   */
  sufficient: boolean;
};

const ALLOWED_HOSTS = new Set(["www.jobkorea.co.kr", "m.jobkorea.co.kr"]);
const MAX_HTML_LENGTH = 5_000_000;

/**
 * Whether an imported job description will actually produce a usable analysis.
 *
 * Delegated entirely to the analyzer's own readiness check — no text-marker
 * guessing. A requirements heading with no recognizable skill is not
 * sufficient, because it still yields an empty analysis. When it isn't
 * sufficient the UI keeps title/company but asks the user to paste the detail.
 */
export function hasSufficientJobDetail(description: string): boolean {
  return inspectJobDescription(description).ready;
}

export class JobImportError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = "JobImportError";
  }
}

export function validateJobKoreaUrl(rawUrl: string): URL {
  let url: URL;
  try {
    url = new URL(rawUrl);
  } catch {
    throw new JobImportError("올바른 잡코리아 채용공고 URL을 입력해 주세요.", 400);
  }
  if (url.protocol !== "https:" || !ALLOWED_HOSTS.has(url.hostname.toLowerCase())) {
    throw new JobImportError("jobkorea.co.kr의 HTTPS 채용공고 URL만 사용할 수 있습니다.", 400);
  }
  if (!/^\/Recruit\/GI_Read\/\d+\/?$/i.test(url.pathname)) {
    throw new JobImportError("잡코리아 채용공고 상세 URL만 사용할 수 있습니다.", 400);
  }
  return url;
}

function decodeHtml(value: string): string {
  const entities: Record<string, string> = { amp: "&", apos: "'", gt: ">", lt: "<", nbsp: " ", quot: '"' };
  return value.replace(/&(#x[\da-f]+|#\d+|[a-z]+);/gi, (match, entity: string) => {
    if (entity[0] !== "#") return entities[entity.toLowerCase()] ?? match;
    const radix = entity[1].toLowerCase() === "x" ? 16 : 10;
    const codePoint = Number.parseInt(entity.slice(radix === 16 ? 2 : 1), radix);
    return Number.isFinite(codePoint) ? String.fromCodePoint(codePoint) : match;
  });
}

export function cleanText(html: string): string {
  return decodeHtml(
    html
      .replace(/<!--[\s\S]*?-->/g, " ")
      .replace(/<(script|style|svg|noscript)\b[\s\S]*?<\/\1>/gi, " ")
      .replace(/<br\s*\/?>/gi, "\n")
      .replace(/<\/(?:div|p|li|section|article|h[1-6]|tr|dt|dd)>/gi, "\n")
      .replace(/<[^>]+>/g, " "),
  )
    .replace(/\r/g, "")
    .replace(/[ \t]+/g, " ")
    .replace(/ *\n */g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .split("\n")
    .filter((line) => !/^\d{8,}$/.test(line.trim()))
    .join("\n")
    .trim();
}

function decodeEscapedMarkup(value: string): string {
  return value
    .replace(/\\u([\da-f]{4})/gi, (_, hex: string) => String.fromCharCode(Number.parseInt(hex, 16)))
    .replace(/\\"/g, '"')
    .replace(/\\n/g, "\n");
}

export function parseJobKoreaDetailHtml(html: string): string {
  if (!html || html.length > MAX_HTML_LENGTH) return "";
  const decoded = decodeEscapedMarkup(html);
  const markers = ["template_common_title", "detailed-summary-header"];
  const markerIndex = markers
    .map((marker) => decoded.indexOf(marker))
    .filter((index) => index >= 0)
    .sort((left, right) => left - right)[0];
  if (markerIndex === undefined) return "";

  const scriptStart = decoded.lastIndexOf("<script", markerIndex);
  const scriptEnd = decoded.indexOf("</script>", markerIndex);
  if (scriptStart < 0 || scriptEnd < 0) return "";

  const serializedBlock = decoded.slice(scriptStart, scriptEnd);
  const firstTag = serializedBlock.indexOf("<", serializedBlock.indexOf(">") + 1);
  const closingTags = [...serializedBlock.matchAll(/<\/[a-z][^>]*>/gi)];
  const lastClosingTag = closingTags.at(-1);
  if (firstTag < 0 || !lastClosingTag?.index) return "";

  return cleanText(serializedBlock.slice(firstTag, lastClosingTag.index + lastClosingTag[0].length));
}

export function metaContent(html: string, property: string): string {
  const escaped = property.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const patterns = [
    new RegExp(`<meta[^>]+(?:property|name)=["']${escaped}["'][^>]+content=["']([^"']*)["'][^>]*>`, "i"),
    new RegExp(`<meta[^>]+content=["']([^"']*)["'][^>]+(?:property|name)=["']${escaped}["'][^>]*>`, "i"),
  ];
  for (const pattern of patterns) {
    const match = html.match(pattern);
    if (match) return cleanText(match[1]);
  }
  return "";
}

export function parseJobKoreaHtml(
  html: string,
  sourceUrl: string,
  fetchedAt = new Date().toISOString(),
): ImportedJobPosting {
  if (!html || html.length > MAX_HTML_LENGTH) {
    throw new JobImportError("채용공고 응답이 비어 있거나 너무 큽니다.", 422);
  }
  const title = metaContent(html, "og:title") || cleanText(html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1] ?? "");
  const company = title.split(/\s+채용\s+-\s+/)[0]?.trim() ?? "";
  const mainHtml =
    html.match(/<main\b[^>]*>([\s\S]*?)<\/main>/i)?.[1] ??
    html.match(/<body\b[^>]*>([\s\S]*?)<\/body>/i)?.[1] ??
    html;
  const description = cleanText(mainHtml);
  if (description.length < 100) {
    throw new JobImportError("채용공고 본문을 찾지 못했습니다. 공개된 잡코리아 상세 공고인지 확인해 주세요.", 422);
  }
  return {
    source: "jobkorea",
    sourceUrl,
    title: title.replace(/\s*\|\s*잡코리아\s*$/i, "").trim(),
    company,
    description,
    fetchedAt,
    sufficient: hasSufficientJobDetail(description),
  };
}

export async function importJobKoreaPosting(rawUrl: string): Promise<ImportedJobPosting> {
  const url = validateJobKoreaUrl(rawUrl);
  const mobileUrl = new URL(url);
  mobileUrl.hostname = "m.jobkorea.co.kr";
  const response = await fetch(mobileUrl, {
    cache: "no-store",
    redirect: "error",
    headers: {
      Accept: "text/html,application/xhtml+xml",
      "User-Agent": "CareerDiff/0.1 (job posting importer)",
    },
    signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) {
    throw new JobImportError(`잡코리아가 채용공고 요청을 거절했습니다. (HTTP ${response.status})`, 502);
  }
  const contentLength = Number(response.headers.get("content-length") ?? 0);
  if (contentLength > MAX_HTML_LENGTH) throw new JobImportError("채용공고 응답이 너무 큽니다.", 422);
  const posting = parseJobKoreaHtml(await response.text(), url.toString());
  const jobId = url.pathname.match(/\d+/)?.[0];
  if (!jobId) return posting;

  const detailResponse = await fetch(`https://m.jobkorea.co.kr/Recruit/GIReadDetailContentIframe/${jobId}`, {
    cache: "no-store",
    redirect: "error",
    headers: {
      Accept: "text/html,application/xhtml+xml",
      "User-Agent": "CareerDiff/0.1 (job posting importer)",
    },
    signal: AbortSignal.timeout(10_000),
  });
  if (!detailResponse.ok) return posting;
  const detailContentLength = Number(detailResponse.headers.get("content-length") ?? 0);
  if (detailContentLength > MAX_HTML_LENGTH) return posting;

  const detail = parseJobKoreaDetailHtml(await detailResponse.text());
  if (detail.length < 100 || posting.description.includes(detail)) return posting;
  // Getting a detail body does not guarantee an analyzable posting — re-check
  // readiness on the combined text instead of forcing sufficient.
  const description = `${posting.description}\n\n상세요강\n${detail}`;
  return { ...posting, description, sufficient: hasSufficientJobDetail(description) };
}

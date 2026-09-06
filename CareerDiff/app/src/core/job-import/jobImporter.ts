import {
  cleanText,
  hasSufficientJobDetail,
  type ImportedJobPosting,
  importJobKoreaPosting,
  JobImportError,
  metaContent,
} from "./jobKoreaImporter";

export { JobImportError };
export type { ImportedJobPosting };

type JobSource = ImportedJobPosting["source"];
const MAX_HTML_LENGTH = 5_000_000;

type SiteSpec = {
  source: JobSource;
  hosts: string[];
  isDetailUrl: (url: URL) => boolean;
  // Optional host rewrite applied before fetching, so a listing URL that would
  // 301 to another same-site host is fetched directly (redirect stays "error").
  toFetchUrl?: (url: URL) => URL;
};

// Each site is pinned to its own host(s) and detail-page path so the SSRF
// surface stays a strict allow-list, same boundary as the JobKorea importer.
const SITES: SiteSpec[] = [
  {
    source: "jobkorea",
    hosts: ["www.jobkorea.co.kr", "m.jobkorea.co.kr"],
    isDetailUrl: (url) => /^\/Recruit\/GI_Read\/\d+\/?$/i.test(url.pathname),
  },
  {
    source: "saramin",
    hosts: ["www.saramin.co.kr"],
    isDetailUrl: (url) =>
      url.pathname.toLowerCase() === "/zf_user/jobs/relay/view" && /^\d+$/.test(url.searchParams.get("rec_idx") ?? ""),
  },
  {
    source: "incruit",
    // www.incruit.com listing links 301 to job.incruit.com; accept both and
    // fetch the job host directly.
    hosts: ["www.incruit.com", "job.incruit.com"],
    isDetailUrl: (url) =>
      url.pathname.toLowerCase() === "/jobdb_info/jobpost.asp" && /^\d+$/.test(url.searchParams.get("job") ?? ""),
    toFetchUrl: (url) => {
      const fetchUrl = new URL(url);
      fetchUrl.hostname = "job.incruit.com";
      return fetchUrl;
    },
  },
];

export function validateJobUrl(rawUrl: string): { site: SiteSpec; url: URL } {
  let url: URL;
  try {
    url = new URL(rawUrl);
  } catch {
    throw new JobImportError("올바른 채용공고 URL을 입력해 주세요.", 400);
  }
  if (url.protocol !== "https:") {
    throw new JobImportError("HTTPS 채용공고 URL만 사용할 수 있습니다.", 400);
  }
  const site = SITES.find((candidate) => candidate.hosts.includes(url.hostname.toLowerCase()));
  if (!site) {
    throw new JobImportError("잡코리아·사람인·인크루트의 채용공고 URL만 사용할 수 있습니다.", 400);
  }
  if (!site.isDetailUrl(url)) {
    throw new JobImportError("채용공고 상세 페이지 URL만 사용할 수 있습니다.", 400);
  }
  return { site, url };
}

export function parseGenericPosting(
  html: string,
  source: JobSource,
  sourceUrl: string,
  fetchedAt = new Date().toISOString(),
): ImportedJobPosting {
  if (!html || html.length > MAX_HTML_LENGTH) {
    throw new JobImportError("채용공고 응답이 비어 있거나 너무 큽니다.", 422);
  }
  const title = metaContent(html, "og:title") || cleanText(html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1] ?? "");
  const mainHtml =
    html.match(/<main\b[^>]*>([\s\S]*?)<\/main>/i)?.[1] ??
    html.match(/<body\b[^>]*>([\s\S]*?)<\/body>/i)?.[1] ??
    html;
  const description = cleanText(mainHtml);
  if (description.length < 100) {
    throw new JobImportError("채용공고 본문을 찾지 못했습니다. 공개된 상세 공고인지 확인해 주세요.", 422);
  }
  const company = metaContent(html, "og:site_name") || title.split(/\s*[|\-–]\s*/)[0]?.trim() || "";
  return {
    source,
    sourceUrl,
    title,
    company,
    description,
    fetchedAt,
    sufficient: hasSufficientJobDetail(description),
  };
}

async function importGenericPosting(site: SiteSpec, url: URL): Promise<ImportedJobPosting> {
  const fetchUrl = site.toFetchUrl?.(url) ?? url;
  const response = await fetch(fetchUrl, {
    cache: "no-store",
    redirect: "error",
    headers: {
      Accept: "text/html,application/xhtml+xml",
      "User-Agent": "CareerDiff/0.1 (job posting importer)",
    },
    signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) {
    throw new JobImportError(`채용사이트가 요청을 거절했습니다. (HTTP ${response.status})`, 502);
  }
  const contentLength = Number(response.headers.get("content-length") ?? 0);
  if (contentLength > MAX_HTML_LENGTH) {
    throw new JobImportError("채용공고 응답이 너무 큽니다.", 422);
  }
  return parseGenericPosting(await response.text(), site.source, url.toString());
}

/**
 * Imports a posting from any supported site. JobKorea keeps its specialized
 * path (mobile rewrite + detail iframe); Saramin/Incruit use the generic
 * best-effort parse. Every site shares the same `sufficient` fallback, so a
 * summary-only result is flagged for manual paste rather than silently thin.
 */
export async function importJobPosting(rawUrl: string): Promise<ImportedJobPosting> {
  const { site, url } = validateJobUrl(rawUrl);
  if (site.source === "jobkorea") {
    return importJobKoreaPosting(url.toString());
  }
  return importGenericPosting(site, url);
}

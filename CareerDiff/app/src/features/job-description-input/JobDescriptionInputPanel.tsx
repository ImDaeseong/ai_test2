"use client";

import { useState } from "react";

export const JOB_DESCRIPTION_MIN_LENGTH = 30;

export function isJobDescriptionValid(value: string): boolean {
  return value.trim().length >= JOB_DESCRIPTION_MIN_LENGTH;
}

export type JobDescriptionInputPanelProps = {
  value: string;
  onChange: (value: string) => void;
};

export function JobDescriptionInputPanel({ value, onChange }: JobDescriptionInputPanelProps) {
  const [touched, setTouched] = useState(false);
  const [jobUrl, setJobUrl] = useState("");
  const [importStatus, setImportStatus] = useState<"idle" | "loading" | "error" | "warning" | "done">("idle");
  const [importMessage, setImportMessage] = useState("");
  const trimmedLength = value.trim().length;
  const isEmpty = trimmedLength === 0;
  const isTooShort = !isEmpty && trimmedLength < JOB_DESCRIPTION_MIN_LENGTH;

  async function importJobPosting() {
    setImportStatus("loading");
    setImportMessage("");
    try {
      const response = await fetch("/api/jobs/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: jobUrl }),
      });
      const body = (await response.json()) as {
        job?: { description: string; sufficient?: boolean; title?: string; company?: string };
        error?: { message: string };
      };
      if (!response.ok || !body.job) {
        setImportStatus("error");
        setImportMessage(body.error?.message ?? "채용공고를 가져오지 못했습니다.");
        return;
      }
      const job = body.job;
      if (job.sufficient === false) {
        // Partial import: the site rendered the real detail client-side, so we
        // only got a summary. Don't populate the analyzable field with that
        // noise — name what we identified and require a manual paste.
        setImportStatus("warning");
        const label = [job.company, job.title].filter(Boolean).join(" · ");
        setImportMessage(
          `${label ? `'${label}' ` : ""}공고의 상세 요강을 자동으로 가져오지 못했습니다. 공고의 상세 모집요강을 복사해 아래 입력란에 붙여넣어 주세요.`,
        );
        return;
      }
      onChange(job.description);
      setImportStatus("done");
      setImportMessage("채용공고를 불러왔습니다.");
    } catch {
      setImportStatus("error");
      setImportMessage("네트워크 오류로 채용공고를 가져오지 못했습니다.");
    }
  }

  return (
    <div className="flex flex-col gap-2 rounded-2xl border border-violet-100 bg-white p-5 shadow-sm shadow-violet-200/40">
      <label htmlFor="job-description" className="text-sm font-bold text-violet-900">
        채용공고
      </label>
      <p className="text-xs text-neutral-500">
        공고 페이지에서 상세 모집요강을 드래그해 복사(Ctrl+C)한 뒤 붙여넣는 것이 가장 정확합니다.
        아래 URL 자동 가져오기는 사이트에 따라 요약만 수집될 수 있습니다.
      </p>
      <textarea
        id="job-description"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onBlur={() => setTouched(true)}
        rows={10}
        placeholder="공고의 상세 모집요강을 복사해 붙여넣으세요."
        className="w-full resize-y rounded-xl border border-violet-100 p-3 text-sm focus:border-violet-400 focus:ring-2 focus:ring-violet-200 focus:outline-none"
      />
      <div className="flex min-h-[1rem] items-center justify-between text-xs text-neutral-500">
        <span>{trimmedLength.toLocaleString()}자</span>
        {touched && isEmpty && <span role="alert" className="text-red-600">채용공고를 입력해 주세요.</span>}
        {touched && isTooShort && (
          <span role="alert" className="text-red-600">최소 {JOB_DESCRIPTION_MIN_LENGTH}자 이상 입력해 주세요.</span>
        )}
      </div>

      <div className="mt-1 flex flex-col gap-1 rounded-xl border border-violet-100 bg-violet-50/60 p-3">
        <label htmlFor="job-url" className="text-xs font-medium text-neutral-600">
          채용공고 URL
        </label>
        <p className="text-xs text-neutral-400">
          잡코리아·사람인·인크루트 상세공고를 자동으로 가져옵니다. 사이트에 따라 요약만 수집될 수 있으니, 정확한 분석을 위해
          위 입력란에 상세 모집요강을 직접 붙여넣는 것을 권장합니다.
        </p>
        <div className="flex gap-2">
          <input
            id="job-url"
            type="url"
            value={jobUrl}
            onChange={(event) => setJobUrl(event.target.value)}
            placeholder="잡코리아·사람인·인크루트 상세공고 URL"
            className="min-w-0 flex-1 rounded-xl border border-violet-100 bg-white p-2 text-sm focus:border-violet-400 focus:ring-2 focus:ring-violet-200 focus:outline-none"
          />
          <button
            type="button"
            onClick={importJobPosting}
            disabled={!jobUrl.trim() || importStatus === "loading"}
            className="rounded-full border border-violet-200 bg-white px-3 py-2 text-sm font-semibold text-violet-700 hover:bg-violet-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {importStatus === "loading" ? "가져오는 중..." : "공고 가져오기"}
          </button>
        </div>
        {importMessage && (
          <p
            role={importStatus === "error" || importStatus === "warning" ? "alert" : "status"}
            className={`text-xs ${
              importStatus === "error"
                ? "text-red-600"
                : importStatus === "warning"
                  ? "text-amber-700"
                  : "text-green-700"
            }`}
          >
            {importMessage}
          </p>
        )}
      </div>
    </div>
  );
}

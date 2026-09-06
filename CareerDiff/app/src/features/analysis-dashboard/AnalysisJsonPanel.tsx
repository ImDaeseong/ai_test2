"use client";

import type { CareerDiffAnalysisResult } from "@/core/types";
import { loadValidationCases } from "@/core/validation/analysisValidationStore";

function downloadJson(filename: string, value: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function AnalysisJsonPanel({
  result,
  validationCount,
}: {
  result: CareerDiffAnalysisResult;
  validationCount: number;
}) {
  return (
    <section className="rounded-2xl border border-violet-100 bg-violet-50/60 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-bold text-violet-900">분석 결과 JSON</h2>
          <p className="text-xs text-neutral-600">
            이 브라우저에 검증 데이터 {validationCount}건이 누적되어 있습니다. 이 기록은 결과 검토용이며, 누적되어도 분석
            품질이 올라가지는 않습니다.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => downloadJson(`careerdiff-result-${Date.now()}.json`, result)}
            className="rounded-full border border-violet-200 bg-white px-3 py-2 text-sm font-semibold text-violet-700 hover:bg-violet-50"
          >
            현재 결과 JSON 다운로드
          </button>
          <button
            type="button"
            onClick={() => downloadJson(`careerdiff-validation-cases-${Date.now()}.json`, loadValidationCases())}
            className="rounded-full border border-violet-200 bg-white px-3 py-2 text-sm font-semibold text-violet-700 hover:bg-violet-50"
          >
            누적 검증 데이터 다운로드
          </button>
        </div>
      </div>
      <details className="mt-3">
        <summary className="cursor-pointer text-sm font-semibold text-violet-700">JSON 원문 보기</summary>
        <pre className="mt-2 max-h-96 overflow-auto whitespace-pre-wrap rounded-xl bg-neutral-900 p-3 text-xs text-neutral-100">
          {JSON.stringify(result, null, 2)}
        </pre>
      </details>
    </section>
  );
}

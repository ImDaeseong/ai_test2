"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  loadValidationCases,
  type AnalysisValidationCase,
} from "@/core/validation/analysisValidationStore";
import { AnalysisDashboard } from "@/features/analysis-dashboard/AnalysisDashboard";
import { ValidationCaseHistoryPanel } from "@/features/analysis-dashboard/ValidationCaseHistoryPanel";

/**
 * Browses every accumulated validation case (data/*.json on the server, with
 * this browser's localStorage as a fetch-failure fallback). Kept off the
 * main page on purpose (docs/ARCHITECTURE.md): that list only grows and is
 * checked occasionally, so fetching it belongs behind a link/route the user
 * opts into, not on every analyzer page load.
 */
export default function ValidationHistoryPage() {
  const [loading, setLoading] = useState(true);
  const [cases, setCases] = useState<AnalysisValidationCase[]>([]);
  const [selected, setSelected] = useState<AnalysisValidationCase | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      // loadValidationCases never throws (it catches its own storage/parse
      // errors and returns []), so a fetch failure always has a usable
      // fallback -- there is no separate "failed to load" state to show.
      let loaded: AnalysisValidationCase[];
      try {
        const response = await fetch("/api/validation-cases");
        if (!response.ok) throw new Error("failed to load validation cases");
        const body = (await response.json()) as { cases: AnalysisValidationCase[] };
        loaded = body.cases;
      } catch {
        loaded = loadValidationCases();
      }
      if (cancelled) return;
      setCases(loaded);
      setSelected(loaded.length > 0 ? loaded[loaded.length - 1] : null);
      setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  function handleSelect(validationCase: AnalysisValidationCase) {
    setSelected(validationCase);
  }

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-10">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="bg-gradient-to-r from-violet-700 to-fuchsia-600 bg-clip-text text-3xl font-extrabold text-transparent">
            분석 히스토리
          </h1>
          <p className="mt-1 text-sm text-neutral-600">이 서버에 누적된 모든 분석 결과를 훑어보고 다시 열어볼 수 있습니다.</p>
        </div>
        <Link
          href="/"
          className="shrink-0 rounded-full border border-violet-200 bg-white px-4 py-2 text-sm font-semibold text-violet-700 shadow-sm hover:bg-violet-50"
        >
          분석하기로 돌아가기
        </Link>
      </header>

      {loading && <p className="text-sm text-neutral-500">불러오는 중...</p>}
      {!loading && cases.length === 0 && (
        <p className="text-sm text-neutral-500">아직 누적된 분석 결과가 없습니다.</p>
      )}

      <ValidationCaseHistoryPanel cases={cases} selectedCaseId={selected?.id ?? null} onSelect={handleSelect} />

      {selected && <AnalysisDashboard result={selected.result} />}
    </main>
  );
}

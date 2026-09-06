import type { AnalysisValidationCase } from "@/core/validation/analysisValidationStore";

function formatDate(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString("ko-KR");
}

function snippet(text: string, length: number): string {
  const trimmed = text.trim();
  return trimmed.length > length ? `${trimmed.slice(0, length)}...` : trimmed;
}

/**
 * Lists every accumulated validation case so past analyses can be browsed and
 * reopened, not only downloaded as one JSON blob (AnalysisJsonPanel). Each
 * row also surfaces relatedSkillGuidance's count — the ontology-bridge output
 * — since that is what distinguishes one case's analysis from a bare score.
 */
export function ValidationCaseHistoryPanel({
  cases,
  selectedCaseId,
  onSelect,
}: {
  cases: AnalysisValidationCase[];
  selectedCaseId: string | null;
  onSelect: (validationCase: AnalysisValidationCase) => void;
}) {
  if (cases.length === 0) return null;

  const ordered = [...cases].reverse();

  return (
    <section
      aria-labelledby="validation-case-history-heading"
      className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm shadow-violet-200/40"
    >
      <h2 id="validation-case-history-heading" className="text-sm font-bold text-violet-900">
        분석 히스토리 ({cases.length}건)
      </h2>
      <ul className="mt-3 flex max-h-[28rem] flex-col gap-2 overflow-y-auto pr-1">
        {ordered.map((item) => {
          const selected = item.id === selectedCaseId;
          return (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => onSelect(item)}
                aria-pressed={selected}
                className={`w-full rounded-xl border p-3 text-left text-sm ${
                  selected ? "border-violet-400 bg-violet-50" : "border-violet-100 bg-white hover:bg-violet-50/50"
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-semibold text-neutral-800">{snippet(item.jobDescription, 40)}</span>
                  <span className="text-xs text-neutral-500">{formatDate(item.createdAt)}</span>
                </div>
                <div className="mt-1 flex flex-wrap gap-2 text-xs text-neutral-600">
                  <span className="rounded-full bg-violet-100 px-2 py-0.5 font-medium text-violet-700">
                    적합도 {item.result.fitScore.total}점
                  </span>
                  <span>연관 기술 가이드 {item.result.relatedSkillGuidance.length}건</span>
                </div>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

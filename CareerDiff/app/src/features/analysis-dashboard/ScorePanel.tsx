import type { FitScore } from "@/core/types";

export function ScorePanel({ fitScore, summary }: { fitScore: FitScore; summary: string }) {
  return (
    <section
      aria-labelledby="score-panel-heading"
      className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm shadow-violet-200/40"
    >
      <h2 id="score-panel-heading" className="text-sm font-bold text-violet-900">
        적합도 점수
      </h2>
      <p className="mt-1 bg-gradient-to-r from-violet-600 to-fuchsia-500 bg-clip-text text-4xl font-extrabold text-transparent">
        {fitScore.total}
        <span className="text-base font-normal text-neutral-500">/100</span>
      </p>
      <p className="mt-2 text-sm text-neutral-700">{summary}</p>
      {fitScore.categories.length === 0 ? (
        <p className="mt-3 text-sm text-neutral-400">세부 점수 항목이 없습니다.</p>
      ) : (
        <ul className="mt-3 flex flex-col gap-2">
          {fitScore.categories.map((category) => (
            <li key={category.label} className="flex items-start justify-between gap-3 text-sm">
              <div>
                <span className="font-medium text-neutral-800">{category.label}</span>
                <p className="text-xs text-neutral-500">{category.reason}</p>
              </div>
              <span className="shrink-0 rounded-full bg-violet-100 px-2 py-0.5 font-semibold text-violet-700">
                {category.score}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

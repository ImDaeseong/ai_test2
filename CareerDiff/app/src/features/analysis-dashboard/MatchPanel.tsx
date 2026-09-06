import type { MatchItem, MatchResult } from "@/core/types";

const SECTION_STYLE: Record<MatchItem["status"], { title: string; badge: string }> = {
  strong: { title: "강한 매칭", badge: "bg-emerald-100 text-emerald-800" },
  weak: { title: "약한 매칭", badge: "bg-amber-100 text-amber-800" },
  missing: { title: "누락된 증거", badge: "bg-neutral-200 text-neutral-700" },
  risk: { title: "리스크", badge: "bg-red-100 text-red-800" },
};

function MatchList({ status, items }: { status: MatchItem["status"]; items: MatchItem[] }) {
  const style = SECTION_STYLE[status];
  return (
    <div>
      <h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">
        <span className={`rounded-full px-2 py-0.5 ${style.badge}`}>{style.title}</span>
        <span>{items.length}</span>
      </h3>
      {items.length === 0 ? (
        <p className="mt-1 text-sm text-neutral-400">해당 항목이 없습니다.</p>
      ) : (
        <ul className="mt-2 flex flex-col gap-2">
          {items.map((item) => (
            <li key={`${status}-${item.requirement}`} className="text-sm">
              <p className="font-medium text-neutral-800">{item.requirement}</p>
              <p className="text-neutral-600">{item.reason}</p>
              {item.evidenceSnippet && <p className="text-xs text-neutral-400">근거: {item.evidenceSnippet}</p>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function MatchPanel({ matches }: { matches: MatchResult }) {
  return (
    <section
      aria-labelledby="match-panel-heading"
      className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm shadow-violet-200/40"
    >
      <h2 id="match-panel-heading" className="text-sm font-bold text-violet-900">
        매칭 결과
      </h2>
      <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <MatchList status="strong" items={matches.strong} />
        <MatchList status="weak" items={matches.weak} />
        <MatchList status="missing" items={matches.missing} />
        <MatchList status="risk" items={matches.risks} />
      </div>
    </section>
  );
}

import type { MiniProjectRecommendation } from "@/core/types";

export function MiniProjectPanel({ miniProjects }: { miniProjects: MiniProjectRecommendation[] }) {
  return (
    <section
      aria-labelledby="mini-project-panel-heading"
      className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm shadow-violet-200/40"
    >
      <h2 id="mini-project-panel-heading" className="text-sm font-bold text-violet-900">
        보완 프로젝트 추천
      </h2>
      {miniProjects.length === 0 ? (
        <p className="mt-2 text-sm text-neutral-400">추천할 프로젝트가 없습니다.</p>
      ) : (
        <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
          {miniProjects.map((project) => (
            <article key={project.title} className="rounded-xl border border-violet-100 bg-violet-50/40 p-3">
              <h3 className="text-sm font-semibold text-neutral-800">{project.title}</h3>
              <p className="mt-1 text-xs text-neutral-500">{project.goal}</p>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">대상 갭</p>
              <div className="mt-1 flex flex-wrap gap-1">
                {project.targetGaps.map((gap) => (
                  <span key={gap} className="rounded-full bg-violet-100 px-2 py-0.5 text-xs font-medium text-violet-700">
                    {gap}
                  </span>
                ))}
              </div>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">산출물</p>
              <ul className="mt-1 list-disc pl-4 text-xs text-neutral-700">
                {project.deliverables.map((deliverable) => (
                  <li key={deliverable}>{deliverable}</li>
                ))}
              </ul>
              <p className="mt-2 text-xs text-neutral-500">예상 소요: {project.suggestedDurationDays}일</p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

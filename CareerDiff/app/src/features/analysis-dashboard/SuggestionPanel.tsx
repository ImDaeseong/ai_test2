import type { ResumeSuggestions } from "@/core/types";
import { CopyButton } from "./CopyButton";

export function SuggestionPanel({ resumeSuggestions }: { resumeSuggestions: ResumeSuggestions }) {
  const hasAnything =
    resumeSuggestions.bullets.length > 0 ||
    resumeSuggestions.projectDescriptions.length > 0 ||
    resumeSuggestions.skillPriority.length > 0 ||
    resumeSuggestions.atsKeywords.length > 0;

  return (
    <section
      aria-labelledby="suggestion-panel-heading"
      className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm shadow-violet-200/40"
    >
      <h2 id="suggestion-panel-heading" className="text-sm font-bold text-violet-900">
        이력서 개선 제안
      </h2>
      {!hasAnything ? (
        <p className="mt-2 text-sm text-neutral-400">제안이 없습니다.</p>
      ) : (
        <div className="mt-3 flex flex-col gap-4">
          {resumeSuggestions.bullets.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-neutral-500">이력서 불릿</h3>
              <ul className="mt-1 flex flex-col gap-2">
                {resumeSuggestions.bullets.map((bullet, index) => (
                  <li key={`${bullet}-${index}`} className="flex items-start justify-between gap-2 text-sm text-neutral-800">
                    <span>{bullet}</span>
                    <CopyButton text={bullet} />
                  </li>
                ))}
              </ul>
            </div>
          )}
          {resumeSuggestions.projectDescriptions.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-neutral-500">프로젝트 설명</h3>
              <ul className="mt-1 flex flex-col gap-2">
                {resumeSuggestions.projectDescriptions.map((description, index) => (
                  <li key={`${description}-${index}`} className="flex items-start justify-between gap-2 text-sm text-neutral-800">
                    <span>{description}</span>
                    <CopyButton text={description} />
                  </li>
                ))}
              </ul>
            </div>
          )}
          {resumeSuggestions.skillPriority.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-neutral-500">스킬 우선순위</h3>
              <ol className="mt-1 list-decimal pl-5 text-sm text-neutral-800">
                {resumeSuggestions.skillPriority.map((skill, index) => (
                  <li key={`${skill}-${index}`}>{skill}</li>
                ))}
              </ol>
            </div>
          )}
          {resumeSuggestions.atsKeywords.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-neutral-500">ATS 키워드</h3>
              <div className="mt-1 flex flex-wrap gap-1.5">
                {resumeSuggestions.atsKeywords.map((keyword, index) => (
                  <span
                    key={`${keyword}-${index}`}
                    className="rounded-full bg-violet-100 px-2.5 py-0.5 text-xs font-medium text-violet-700"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

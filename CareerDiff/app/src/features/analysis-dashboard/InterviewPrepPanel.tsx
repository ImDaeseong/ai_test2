import type { InterviewPrep } from "@/core/types";

export function InterviewPrepPanel({ interviewPrep }: { interviewPrep: InterviewPrep }) {
  const hasAnything =
    interviewPrep.questions.length > 0 || interviewPrep.weakAreas.length > 0 || interviewPrep.sevenDayPlan.length > 0;

  return (
    <section
      aria-labelledby="interview-prep-panel-heading"
      className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm shadow-violet-200/40"
    >
      <h2 id="interview-prep-panel-heading" className="text-sm font-bold text-violet-900">
        면접 준비
      </h2>
      {!hasAnything ? (
        <p className="mt-2 text-sm text-neutral-400">준비 항목이 없습니다.</p>
      ) : (
        <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-neutral-500">예상 질문</h3>
            <ul className="mt-1 list-disc pl-4 text-sm text-neutral-800">
              {interviewPrep.questions.map((question) => (
                <li key={question}>{question}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-neutral-500">약점 영역</h3>
            <ul className="mt-1 list-disc pl-4 text-sm text-neutral-800">
              {interviewPrep.weakAreas.map((area) => (
                <li key={area}>{area}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-neutral-500">7일 준비 플랜</h3>
            <ol className="mt-1 list-decimal pl-4 text-sm text-neutral-800">
              {interviewPrep.sevenDayPlan.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </div>
        </div>
      )}
    </section>
  );
}

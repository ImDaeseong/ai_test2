import type { JobRequirements, RequirementItem } from "@/core/types";

function RequirementList({ title, items }: { title: string; items: RequirementItem[] }) {
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wide text-neutral-500">{title}</h3>
      {items.length === 0 ? (
        <p className="mt-1 text-sm text-neutral-400">추출된 항목이 없습니다.</p>
      ) : (
        <ul className="mt-1 flex flex-col gap-1">
          {items.map((item) => (
            <li key={item.id} className="text-sm text-neutral-800">
              {item.label}
              {item.evidenceSnippet && <span className="ml-1 text-xs text-neutral-500">— {item.evidenceSnippet}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function RequirementPanel({ jobRequirements }: { jobRequirements: JobRequirements }) {
  return (
    <section
      aria-labelledby="requirement-panel-heading"
      className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm shadow-violet-200/40"
    >
      <h2 id="requirement-panel-heading" className="text-sm font-bold text-violet-900">
        채용 요건
      </h2>
      {jobRequirements.seniority && (
        <p className="mt-1 text-xs text-neutral-500">목표 시니어리티: {jobRequirements.seniority}</p>
      )}
      <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <RequirementList title="필수 스킬" items={jobRequirements.requiredSkills} />
        <RequirementList title="우대 스킬" items={jobRequirements.preferredSkills} />
        <RequirementList title="도메인" items={jobRequirements.domain} />
        <RequirementList title="협업" items={jobRequirements.collaboration} />
        <RequirementList title="딜리버리 기대치" items={jobRequirements.deliveryExpectations} />
      </div>
    </section>
  );
}

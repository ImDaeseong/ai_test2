import type { CareerDiffAnalysisResult } from "@/core/types";
import { InterviewPrepPanel } from "./InterviewPrepPanel";
import { MatchPanel } from "./MatchPanel";
import { MiniProjectPanel } from "./MiniProjectPanel";
import { RelatedSkillPanel } from "./RelatedSkillPanel";
import { RequirementPanel } from "./RequirementPanel";
import { ScorePanel } from "./ScorePanel";
import { SuggestionPanel } from "./SuggestionPanel";

/**
 * Page-level composition for the result view (docs/PRODUCT.md). Display-only:
 * it must not recalculate any analysis logic, only render `result`.
 */
export function AnalysisDashboard({ result }: { result: CareerDiffAnalysisResult }) {
  const requirementCount =
    result.jobRequirements.requiredSkills.length + result.jobRequirements.preferredSkills.length;
  const noMatches = result.matches.strong.length === 0;
  // A 0-match result is valid but easily misread as "nothing happened". Say why
  // and what to do, splitting the two causes: an empty job vs. a real mismatch.
  const noMatchNotice = !noMatches
    ? null
    : requirementCount === 0
      ? "공고에서 비교할 기술 요건을 추출하지 못했습니다. 공고의 상세 모집요강을 붙여넣은 뒤 다시 분석해 주세요."
      : "이 공고의 요구 역량과 직접 일치하는 이력서 근거가 없습니다. 이력서/커리어에 관련 경험을 보강하거나 다른 공고와 비교해 보세요.";

  return (
    <div className="flex flex-col gap-4">
      {noMatchNotice && (
        <p role="status" className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {noMatchNotice}
        </p>
      )}
      <ScorePanel fitScore={result.fitScore} summary={result.summary} />
      <RequirementPanel jobRequirements={result.jobRequirements} />
      <MatchPanel matches={result.matches} />
      <SuggestionPanel resumeSuggestions={result.resumeSuggestions} />
      <MiniProjectPanel miniProjects={result.miniProjects} />
      <RelatedSkillPanel relatedSkillGuidance={result.relatedSkillGuidance} />
      <InterviewPrepPanel interviewPrep={result.interviewPrep} />
    </div>
  );
}

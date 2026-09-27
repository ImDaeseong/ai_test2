# ai_test2 Design

Updated: 2026-09-27

## Purpose

Collect research, career-analysis, animation, and image/video prompt applications with explicit local-versus-external processing choices.

## Stakeholders, concerns, and scenarios

- User: understand when personal or research data stays local and when it leaves the machine.
- Developer: preserve subproject independence and explicit provider boundaries.
- Reviewer: evaluate evidence quality, consent, and generated-media quality separately.
- Representative scenario: select a subproject and processing mode, validate consent and inputs, generate analysis or prompts, then review before export or publication.

## Boundaries

- Each subproject owns its execution and data contract.
- Career and research inputs remain local unless the user explicitly selects an external provider.
- Prompt generation, asset production, and publication are separate stages.

## Main components

- `CareerDiff/`: local or consented external career comparison.
- `music_insight_studio/` and `youtube_research/`: research and analysis workflows.
- `ai_anime/`, `ai_img_video_aiBoygirl/`, and `ai_img_video_prompt_capcut/`: visual prompt pipelines.
- [ARCHITECTURE.md](ARCHITECTURE.md): repository-level component map.

## Detailed structure and views

The detailed implementation and target module boundaries are maintained in [ARCHITECTURE.md](ARCHITECTURE.md); consent and release gates are in [SECURITY_BOUNDARY.md](SECURITY_BOUNDARY.md), [HOLD_CONDITIONS.md](HOLD_CONDITIONS.md), and [VERIFICATION.md](VERIFICATION.md).

### System and contract view

```text
`ai_img_video_aiBoygirl/` or `ai_anime/`
  -> prompt Markdown + CapCut editing map
  -> `ai_img_video_prompt_capcut/`
  -> timeline.json / shot_list.md / CapCut draft

`youtube_research/`, `music_insight_studio/`, and `CareerDiff/`
  -> independent research, local audio, and career-analysis products
```

File contracts?봢diting-map sections, LRC/SRT labels, clip names, timeline JSON, and CapCut draft files?봞re the only intentional cross-project integration. `music_insight_studio` is local-only; `CareerDiff` owns its Next.js boundary and sends job/resume text externally only after the user selects that path.

## Key decisions and tradeoffs

- Make local versus external processing an explicit user choice rather than an implementation detail.
- Separate research conclusions from generated media artifacts because their evidence and review criteria differ.

## Verification and human review

Run the root and subproject test commands documented in README. Research conclusions, personal-data transmission, generated visual quality, and publication remain human-review decisions.

## Evidence basis and limits

This design is informed by [IEEE 1016-2009](https://standards.ieee.org/ieee/1016/4502/), [Kruchten](https://www.cs.ubc.ca/~gregor/teaching/papers/4%2B1view-architecture.pdf), [Parnas (1972)](https://doi.org/10.1145/361598.361623), [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html), and [NIST SSDF 1.1](https://doi.org/10.6028/NIST.SP.800-218). It is evidence-informed, not a formal compliance assessment.

The choice of detailed views is also guided by [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html), whose public abstract specifies architecture descriptions, viewpoints, and model kinds, and the [SEI Views and Beyond approach](https://www.sei.cmu.edu/library/views-and-beyond-the-sei-approach-for-architecture-documentation/), which organizes documentation around views selected for stakeholder use. Only views supported by current repository evidence are included; omitted views are not implied.

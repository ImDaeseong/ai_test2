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

## Key decisions and tradeoffs

- Make local versus external processing an explicit user choice rather than an implementation detail.
- Separate research conclusions from generated media artifacts because their evidence and review criteria differ.

## Verification and human review

Run the root and subproject test commands documented in README. Research conclusions, personal-data transmission, generated visual quality, and publication remain human-review decisions.

## Evidence basis and limits

This design is informed by [IEEE 1016-2009](https://standards.ieee.org/ieee/1016/4502/), [Kruchten](https://www.cs.ubc.ca/~gregor/teaching/papers/4%2B1view-architecture.pdf), [Parnas (1972)](https://doi.org/10.1145/361598.361623), [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html), and [NIST SSDF 1.1](https://doi.org/10.6028/NIST.SP.800-218). It is evidence-informed, not a formal compliance assessment.

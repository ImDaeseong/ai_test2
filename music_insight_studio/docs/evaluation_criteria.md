# Music Evaluation Criteria

이 문서는 `ai_test3` 음악 분석 도구의 평가 기준 원본입니다. 점수는 흥행 보장이 아니라, 곡들을 같은 기준으로 비교하기 위한 의사결정 보조값입니다.

## Reference Hierarchy

1. Measurable audio evidence: audio file에서 직접 추출한 BPM, Key, LUFS, RMS, dynamic range, frequency balance, energy curve.
2. Production criteria: `ai_test1` 저장소의 `music_skills*`와 `music_beats`의 프로듀스/사운드/믹싱 기준 (로컬 인접 저장소, 경로 비공개).
3. Lyric and hook criteria: `ai_test1` 저장소의 `music_lyric/LYRIC_MASTER_PROMPT.md`와 `LYRIC_REVIEW_PROMPT.md`의 훅, 가사, 현대어, Suno 사용성 기준.
4. Channel and release criteria: `hermes-agents/ai-workspace` 저장소의 `suno/catalog-template.md`, `youtube/`, `AI_PARTNER.md`, `HERMES_CONTEXT_RULES.md`의 `justaimusickr` 방향성과 선별 기준.
5. External platform criteria: 스트리밍 LUFS, 플랫폼별 권장값, 유튜브/숏폼 트렌드는 구현 직전 최신 공식/신뢰 자료로 재검증한다.

## Score Groups

MVP는 100점 단일 총점보다, 다음 하위 점수를 먼저 보여준다.

| Group | Weight | Source | Purpose |
|---|---:|---|---|
| Technical Audio | 25 | audio analysis | 음원 자체의 측정 품질 |
| Production and Mix | 20 | audio + ai_test1 production docs | 믹스, 마스터링, 질감, 공간감 |
| Songwriting and Hook | 20 | music_lyric docs | 후렴, 첫 3초, 반복성, 가사 전달력 |
| AI Naturalness | 15 | Suno/AI checklist | AI 티, 반복 패턴, 보컬 자연스러움 |
| Market and Channel Fit | 20 | ai-workspace channel docs | 유튜브/숏폼/스트리밍/채널 적합성 |

## Technical Audio Criteria

Measured fields:

- duration
- BPM estimate and confidence
- estimated key
- LUFS when available
- RMS mean/std
- dynamic range proxy
- spectral centroid and rolloff
- frequency band energy
- section energy curve

Evaluation rules:

- 분석값은 `detected`와 `estimated`로 표시한다.
- BPM/Key는 틀릴 수 있으므로 확정값처럼 말하지 않는다.
- LUFS와 dynamic range는 장르별로 다르게 해석한다.
- 저음/고음 부족 또는 과다는 주파수 대역 비율로 근거를 남긴다.

## Production and Mix Criteria

Evaluate:

- Low-end control: sub/bass가 탁하거나 과하지 않은가.
- Mid clarity: 보컬/멜로디 중심 대역이 묻히지 않는가.
- Presence: 훅과 보컬이 선명한가.
- High-end brightness: 답답하거나 과하게 날카롭지 않은가.
- Stereo/spatial impression: 공간감이 있지만 중심이 비지 않는가.
- Dynamic movement: 벌스, 프리코러스, 후렴의 에너지 차이가 있는가.
- Mastering readiness: 플랫폼 노멀라이즈 후에도 죽은 소리처럼 들릴 가능성이 낮은가.

Important note:

- `ai_test1` 문서의 LUFS 표와 플랫폼 값은 내부 기준으로만 사용한다. 플랫폼 정책은 바뀔 수 있으므로 배포 기능 구현 전 최신 자료로 재검증한다.

## Songwriting and Hook Criteria

From `music_lyric` 기준을 따른다.

Evaluate:

- 첫 3초에 귀를 잡는 문장/소리/멜로디 포인트가 있는가.
- 후렴 첫 줄이 제목 후보처럼 작동하는가.
- 후렴이 짧고 반복 가능하며 따라 부르기 쉬운가.
- 벌스가 설명이 아니라 장면, 행동, 사물로 감정을 보여주는가.
- 프리코러스가 후렴으로 향하는 압력을 만든는가.
- 브리지가 새 정보나 관점 전환을 주는가.
- 마지막 후렴이 단순 반복이 아니라 의미 또는 편곡을 확장하는가.
- 현대 한국어 기준에서 어색한 번역투, 낡은 문어체, 금방 낡을 밈이 핵심 훅을 차지하지 않는가.

Hook subscore:

- memorability
- singability/pronunciation
- title fit
- short-form cut potential

## AI Naturalness Criteria

Evaluate:

- 보컬 발음이 뭉개지거나 기계적으로 들리는가.
- 같은 멜로디/리듬/가사 패턴이 필요 이상 반복되는가.
- 섹션 전환이 갑작스럽거나 무작위처럼 느껴지는가.
- 악기/보컬 레이어가 곡 의도와 맞게 변하는가.
- Suno 스타일 프롬프트의 흔한 문제: 장르 라벨만 나열, 실존 아티스트명 사용, `[ad-lib]`/`[humming]` 라벨만 있고 실제 발음 없음, 라이브/관중 소음 유발 키워드.
- `clean studio mix`, `recording booth take`, `pre-written studio vocal take`처럼 스튜디오/비즉흥 앵커가 필요한 경우 반영되었는가.

## Market and Channel Fit Criteria

From `ai-workspace/suno/catalog-template.md` and channel docs:

- Hook: 기억나는 멜로디나 사인 포인트가 있는가.
- Mood: 감정과 분위기가 분명한가.
- Visual Potential: 이미지/영상으로 확장하기 쉬운가.
- Channel Fit: `justaimusickr` 채널 방향과 맞는가.
- Personal Taste: 사용자가 계속 밀고 싶은 곡인가.

MVP report should separate:

- general marketability
- YouTube fit
- short-form fit
- streaming playlist fit
- `justaimusickr` channel fit

## PASS / REVISE / HOLD

- PASS: 공개 또는 다음 제작 단계로 넘겨도 되는 수준.
- REVISE: 고치면 쓸 수 있는 수준. 리포트에 최대 3개 우선 수정안을 제시한다.
- HOLD: 저작권/실존 인물 복제/민감정보/외부 업로드/보안 위험 또는 분석 신뢰도 부족 때문에 진행 중단.

## Report Requirements

Every score must include:

- score value
- evidence from audio or provided text
- reason in Korean
- uncertainty note when the evidence is weak
- next action

Do not claim:

- guaranteed views
- guaranteed playlist placement
- guaranteed revenue
- exact artist cloning
- exact platform outcome

## Specialist Criteria Documents

The first-pass specialist criteria are split into these source files:

- `docs/composer_criteria.md`
- `docs/lyricist_criteria.md`
- `docs/producer_criteria.md`
- `docs/mixing_criteria.md`
- `docs/mastering_criteria.md`
- `docs/ai_music_criteria.md`
- `docs/market_release_criteria.md`
- `docs/scoring_model.md`

Implementation must treat these files as the detailed criteria source and this document as the consolidated overview.

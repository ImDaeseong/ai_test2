# Lyricist Criteria

작사가 관점의 평가는 훅 문장, 발음성, 장면성, 현대어 자연성, Suno/보컬 전달 안정성을 판단한다.

## Core Questions

- 후렴 첫 줄이 제목 후보처럼 작동하는가.
- 첫 3초 라인이 귀를 잡는가.
- 감정이 직접 설명이 아니라 장면, 행동, 사물, 짧은 말, 침묵으로 드러나는가.
- Verse 1과 Verse 2가 같은 정보를 반복하지 않는가.
- Pre-Chorus는 감정 압력을 올리는가.
- Bridge는 새 정보나 관점 전환을 주는가.
- 후렴은 짧고 반복 가능하며 따라 부르기 쉬운가.
- 현대 한국어 기준에서 어색한 번역투, 낡은 표현, 금방 낡을 밈이 핵심 훅을 차지하지 않는가.

## Evidence Fields

- lyrics text if provided
- section tags
- line count by section
- hook candidates
- repeated phrase count
- Korean/English ratio
- flagged cliche terms
- label-only tags such as `[ad-lib]` or `[humming]`

## Hook Subscore

| Item | Weight | Good Signal |
|---|---:|---|
| Memorability | 30 | 한 줄만 떼어도 곡 감정이 보임 |
| Pronunciation | 25 | 부르기 쉬운 자음/모음 흐름 |
| Title fit | 25 | 제목으로 써도 자연스러움 |
| Short-form fit | 20 | 10-20초 클립으로 잘림 |

## Cliche and Safety Checks

- 기존 곡 제목, 가사, 훅 문구와 실질적으로 유사하면 HOLD.
- 실존 작사가/가수의 문체 복제 요청은 HOLD.
- 진부한 단어만으로 감정을 때우면 REVISE.
- Suno Lyrics에 실제 발음 없는 라벨만 있으면 REVISE.

## PASS / REVISE / HOLD

- PASS: 후렴이 짧고 기억되며, 벌스/브리지 정보가 분명하고 현대어가 자연스럽다.
- REVISE: 훅, 장면성, 음절, 진부함, Suno 태그 안정성 중 일부 개선 필요.
- HOLD: 저작권 복제, 실존 인물 문체/목소리 복제, 민감정보 포함, 혐오/불법 조장.

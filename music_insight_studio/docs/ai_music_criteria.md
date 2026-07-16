# AI Music Criteria

AI 음악 평가는 일반 음악 평가 위에 추가되는 모드다. 사람이 만든 곡, AI 곡, 하이브리드 곡 모두 평가하되, AI 생성 여부가 있거나 의심될 때만 이 기준을 추가한다.

## Applies To

- Suno, Udio, 기타 AI 생성 음악
- 사람이 쓴 가사 + AI 생성 음원
- AI 반주 + 직접 보컬
- 직접 작곡 + AI 편곡/마스터링
- AI 초안 + 사람이 후편집한 곡

## Core Questions

- 보컬 발음이 뭉개지거나 기계적으로 들리는가.
- 감정 표현이 사람처럼 호흡/강약/타이밍을 갖는가.
- 같은 멜로디, 리듬, 가사 패턴이 필요 이상 반복되는가.
- 섹션 전환이 자연스러운가, 갑자기 붙인 것처럼 들리는가.
- 후렴이 중독성 있는 반복인지, AI식 루프 반복인지 구분되는가.
- 프롬프트와 실제 결과가 일치하는가.
- 장르 라벨만 있고 실제 질감/리듬/공간감이 부족한가.
- `[ad-lib]`, `[humming]`처럼 실제 발음 없는 라벨 태그가 문제를 만들었는가.

## Evidence Fields

- declared generation tool if provided
- prompt text if provided
- lyrics text if provided
- section structure
- repeated phrase/motif count
- abrupt energy changes
- vocal clarity proxy
- user notes about AI generation

## AI Naturalness Subscore

| Item | Weight |
|---|---:|
| Vocal naturalness | 25 |
| Repetition control | 20 |
| Section transition | 20 |
| Prompt-result fit | 15 |
| Emotional believability | 10 |
| Artifact risk | 10 |

## PASS / REVISE / HOLD

- PASS: AI 생성 여부와 무관하게 자연스럽고 음악적으로 설득력이 있다.
- REVISE: 반복, 발음, 전환, 프롬프트 태그, 구조 중 일부 수정 또는 재생성이 필요하다.
- HOLD: 실존 인물 목소리/스타일 복제, 저작권 회피 목적, 무단 모방 요청이 있다.

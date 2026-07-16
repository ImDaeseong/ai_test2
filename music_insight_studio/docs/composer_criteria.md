# Composer Criteria

작곡가 관점의 평가는 멜로디, 화성, 리듬, 구조, 긴장과 해소가 곡으로 작동하는지 판단한다. 오디오 분석만으로 확정할 수 없는 항목은 `estimated`로 표시한다.

## Core Questions

- 첫 3-10초 안에 기억될 모티프가 있는가.
- Verse, Pre-Chorus, Chorus가 서로 다른 역할을 하는가.
- 후렴 진입 전 긴장 상승이 있는가.
- 후렴은 곡의 가장 기억되는 멜로디/리듬/화성 지점인가.
- 반복과 변주가 균형을 이루는가.
- Bridge 또는 후반부에 새 정보, 전조, 리듬 변화, 질감 변화가 있는가.
- 마지막 후렴은 단순 반복이 아니라 에너지 또는 의미가 확장되는가.

## Evidence Fields

- detected BPM and confidence
- estimated key
- section energy curve
- chord progression if prompt/metadata is available
- hook position estimate
- chorus energy delta against verse
- repeated motif count if lyrics or sections are available

## Scoring Rubric

| Item | Weight | Good Signal | Weak Signal |
|---|---:|---|---|
| Motif and memorability | 20 | 짧고 반복 가능한 중심 모티프 | 산만하고 기억점 없음 |
| Harmonic direction | 15 | 긴장-해소, 전환, 색채가 있음 | 코드 반복이 기능 없이 평평함 |
| Rhythm and tempo fit | 15 | 장르/감정과 BPM/그루브가 맞음 | 템포가 의도와 충돌 |
| Section architecture | 20 | Verse/Pre/Chorus/Bridge 역할이 다름 | 섹션 차이가 작음 |
| Hook arrival | 15 | 후렴 진입이 명확하고 강함 | 후렴이 벌스와 구분 안 됨 |
| Variation and payoff | 15 | 후반부 확장 또는 반전 있음 | 마지막까지 같은 질감 반복 |

## PASS / REVISE / HOLD

- PASS: 구조와 후렴이 명확하고, 반복 청취를 견딜 작곡적 중심이 있다.
- REVISE: 모티프, 후렴 진입, Bridge, 마지막 후렴 중 1-3개를 개선하면 쓸 수 있다.
- HOLD: 기존 곡의 멜로디/훅/진행을 실질적으로 복제하려는 요청이 있거나 근거 없이 특정 작곡가 복제를 요구한다.

## Report Language

작곡 평가는 “좋다/나쁘다”보다 `어떤 섹션에서 왜 힘이 생기거나 빠지는지`를 설명한다.

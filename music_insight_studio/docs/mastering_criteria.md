# Mastering Criteria

마스터링 관점의 평가는 스트리밍/유튜브 재생에서 과압축, 피크, 음량, 다이내믹 유지 여부를 본다.

## Measurable Fields

- integrated LUFS when pyloudnorm is available
- peak level or true peak when available
- dynamic range proxy
- RMS mean/std
- clipping risk proxy
- spectral balance after mix

## Platform Reference Policy

플랫폼 음량 기준은 바뀔 수 있다. 구현 또는 배포 기능을 만들기 직전 최신 공식/신뢰 자료로 재검증한다. MVP 문서의 값은 내부 비교 기준으로만 사용한다.

## Internal Targets for MVP

- general streaming safety: around -14 LUFS, peak ceiling near -1 dBTP when true peak is available
- YouTube/short-form readiness: loudness consistency without killing transients
- ballad/acoustic: more dynamic movement allowed
- EDM/trap/rock: denser loudness allowed, but clipping and fatigue must be flagged

## Core Questions

- 과하게 눌려서 후렴이 더 커지지 않는가.
- 플랫폼 노멀라이즈 후 평평하고 죽은 소리처럼 들릴 위험이 있는가.
- 피크/클리핑 위험이 있는가.
- 저역과 고역이 마스터링 단계에서 과장되어 번역성이 나빠질 가능성이 있는가.
- 장르와 감정에 맞는 다이내믹이 남아 있는가.

## PASS / REVISE / HOLD

- PASS: 목표 플랫폼에 올려도 큰 음량/피로/클리핑 문제가 예상되지 않는다.
- REVISE: LUFS, 피크, 과압축, 고역 피로, 저역 과다 중 일부 조정 필요.
- HOLD: 파일이 클리핑/왜곡/무음/손상으로 마스터링 평가가 불가능하다.

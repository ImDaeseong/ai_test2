# Docs Index

`ai_test3`의 설계/평가 기준 문서 입구입니다. 전체 문서(루트 문서 포함) 지도는 `INDEX.md`를 참고하세요.

## Read Order

1. `evaluation_criteria.md` - 전체 평가 기준 개요
2. `scoring_model.md` - 점수 산식, 가중치, 모드별 조정
3. `composer_criteria.md` - 작곡가 관점
4. `lyricist_criteria.md` - 작사가 관점
5. `producer_criteria.md` - 프로듀서 관점
6. `mixing_criteria.md` - 믹싱 엔지니어 관점
7. `mastering_criteria.md` - 마스터링 관점
8. `ai_music_criteria.md` - AI 음악 전용 추가 평가
9. `market_release_criteria.md` - A&R/시장/공개 우선순위
10. `reference_sources.md` - 참조 소스와 재사용 판단

## Scope Documents

- `audio_analysis_scope.md` - 오디오 분석 가능 범위
- `ai_music_analysis_scope.md` - AI 음악 분석 가능 범위
- `marketability_scoring.md` - 시장성 점수 초안

## First-Pass Completion Definition

1차 기준 문서 세트는 다음 조건을 만족해야 한다.

- 전문가 관점별 기준 문서가 존재한다.
- 각 문서에 핵심 질문, 증거 필드, PASS/REVISE/HOLD 또는 점수 기준이 있다.
- `evaluation_criteria.md`가 세부 기준 문서를 참조한다.
- `VERIFICATION.md`에 검증 명령이 있다.
- 검증 명령에서 파일 존재와 핵심 헤더가 확인된다.

## Commercial and Feature Design Additions

Read these before converting the local MVP into a public or paid service:

1. `commercial/COMMERCIAL_READINESS.md`
2. `commercial/PRODUCTION_ARCHITECTURE.md`
3. `commercial/WEB_SECURITY.md`
4. `commercial/DATA_RETENTION.md`
5. `commercial/COPYRIGHT_POLICY.md`
6. `features/score_generation.md`

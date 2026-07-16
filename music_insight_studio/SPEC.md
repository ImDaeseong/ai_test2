# Specification

## Purpose

사용자가 제작한 음원 또는 AI 생성 음악을 업로드하면, 오디오 특징 분석과 음악 제작 관점의 평가를 결합해 실행 가능한 한국어 리포트를 제공한다.

## Inputs

- Required: MP3, WAV, FLAC 중 하나의 음원 파일
- Optional: Suno 프롬프트, 가사, 장르 태그, 목표 플랫폼, 비교 대상 곡
- Optional later: stem 파일, 커버 이미지, 레퍼런스 설명

## Outputs

- 요약 점수: 믹스, 마스터링, 후렴 강도, 반복 청취성, 숏폼 적합성, 스트리밍 적합성
- 기술 분석: BPM, Key, 길이, LUFS, RMS, 다이내믹 레인지, 주파수 대역 밸런스
- 음악 분석: 장르 추정, 분위기, 악기 구성 추정, 보컬/후렴/구조 평가
- AI 음악 분석: AI 느낌, 반복 패턴, 보컬 자연스러움, 가사 전달력
- 스타일 제안: 현재 Suno 스타일 요약, 개선된 Suno 스타일 태그
- 우선순위: 헤드룸, 라우드니스, 가사/훅, AI 분석 모드 같은 즉시 개선 포인트
- 개선 제안: 믹싱, 편곡, 구조, 공개 전략
- 저장 형식: Markdown, 한국어 Markdown, JSON, MusicXML(구간 차트 형태 세션 악보)

## MVP Features

1. 단일 음원 파일 업로드
2. numpy/soundfile 기반 BPM/Key/RMS/스펙트럼/섹션 에너지 분석
3. pyloudnorm 사용 가능 시 LUFS 분석
4. 규칙 기반 믹싱/마스터링 평가
5. 규칙 기반 시장성 평가 초안
6. Markdown/한국어 Markdown/JSON 리포트 생성
7. 로컬 Web MVP에서 단일 음원 업로드 후 `AnalysisService`로 같은 리포트 생성
8. Web MVP에서 한국어 리포트를 같은 화면에 표시
9. 분석값 기반 현재/개선 Suno 스타일 제안 표시
10. 리포트 상단에 우선 개선 포인트 표시
11. 분석 실패 시 원인과 재시도 안내 표시
12. MusicXML 세션 차트(구간 에너지 기반) 생성 — CLI는 파일로, Web은 "악보 MusicXML" 클릭 시 새 탭(`/score`)에서 렌더링 + 원문 텍스트 표시. `JSON` 링크도 같은 방식(새 탭)으로 동작해 분석 결과 화면이 사라지지 않음

## Later Features

- Demucs 기반 vocal/drums/bass/other stem 분리
- A곡/B곡 비교 분석
- Suno 프롬프트와 가사 입력을 고급 옵션으로 재도입
- LLM 기반 자연어 평가 보강
- 플레이리스트/숏폼/유튜브별 평가 프로파일

## Reuse Plan

- `Analysis_music/analyzer/audio_analyzer.py`에서 기본 오디오 분석 로직 재사용
- `Analysis_music/analyzer/suno_parser.py`에서 Suno 프롬프트 파싱 로직 재사용
- `Analysis_music/generators/report_gen.py`에서 리포트 구조 아이디어 재사용
- `mp3_daw/engine.py`에서 LUFS, 주파수 대역, 파형 피크, 마스터링 관련 로직 선별 재사용

## Constraints

- 기본 동작은 로컬 파일 처리 중심으로 한다.
- 업로드 파일은 `uploads/`에 보관하되, 기본 정책은 사용자가 명시적으로 저장을 원할 때만 장기 보관한다.
- 분석 결과는 확률적/추정값임을 리포트에 명시한다.
- 외부 API 사용은 별도 설정과 사용자 동의가 있을 때만 허용한다.

## Evaluation Criteria Source

평가 기준은 `docs/evaluation_criteria.md`를 원본으로 삼는다. 구현 단계에서 점수 산식은 이 문서의 Score Groups와 PASS/REVISE/HOLD 기준을 따라야 한다.



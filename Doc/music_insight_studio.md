# 설계 문서 — music_insight_studio

> 로컬 우선 음악 분석 도구 — MP3/WAV/FLAC 업로드 시 BPM/Key/LUFS/주파수 밸런스 분석 + 규칙 기반 믹싱/마스터링/AI 자연스러움/시장성 평가를 한국어 리포트 + MusicXML로 생성
> 외부 API 없음. 필수 의존성: `numpy`, `soundfile`, `pyloudnorm`. 선택 의존성: `librosa`(BPM 1순위), `basic-pitch`(악보 채보 1순위) — 둘 다 미설치 시 내장 폴백 자동 사용.

---

## 1. 목적과 범위

음악 제작/발매 준비 중 음원 파일을 업로드해 BPM, Key, 믹싱 상태, AI 음악 자연스러움, 시장성을 분석한 한국어 리포트를 얻는다. 다른 5개 프로젝트(MV/프롬프트 생성 파이프라인)와 파일·의존성 공유 없이 완전 독립 실행된다(2026-07-17 `ai_test3`에서 이동).

**입력**: MP3/WAV/FLAC(필수), Suno 프롬프트·가사·장르·목표 플랫폼(선택, CLI만)
**출력**: `analysis_report.md`, `analysis_report.ko.md`, `analysis_report.json`, `analysis_lead_sheet.musicxml`
**비목표**: 특정 가수 복제, 외부 플랫폼 자동 업로드, 스트리밍 성과 보장, 완전한 음악학적 채보/전문 마스터링 대체

---

## 2. 아키텍처

```
app/
  analyzers/   audio.py(DSP 분석), text.py(가사/프롬프트 분석)
  scoring/     engine.py(오케스트레이션), rubric.py, specialists.py(항목별 채점), base.py
  notation/    transcription.py(오디오→음표), musicxml_writer.py(리드시트 생성)
  reports/     markdown.py, korean_markdown.py, json_report.py
  services/    analysis_service.py(analyzers+scoring+reports 조합)
  web/         server.py(stdlib http.server), security.py(업로드 검증)
  cli/         __main__.py
```

각 서브패키지가 독립 모듈 경계를 가진 상태로 이미 완성돼 있어(2026-07-15 `PROJECT_STRUCTURE.md` 감사에서 5개 폴더 전부 orphan 아님 확인), `ROADMAP.md`의 Phase 4(대형 스크립트 모듈 분리) 대상이 아니다.

---

## 3. 데이터 흐름

```
업로드 오디오 (wav/mp3/flac)
      │
      ▼
AudioAnalyzer.analyze()          ─ BPM(librosa 우선, 없으면 autocorrelation)
  │                                Key(FFT 스펙트럼 → 12 pitch class, 벡터화됨)
  │                                LUFS(pyloudnorm), 주파수 밸런드(7밴드)
  ▼
ScoringEngine.evaluate()         ─ 작곡/작사/프로듀싱/믹싱/마스터링/시장성 룰 기반 채점
  │                                (docs/*.md에 각 기준 문서화)
  ▼
ScoreTranscriber.transcribe()    ─ basic-pitch 있으면 실제 채보, 없으면 heuristic
  │                                90초 캡 내에서만 (local-performance 트레이드오프)
  ▼
Report writers                   ─ md/ko.md/json/musicxml 4종 동시 생성
```

**핵심 트레이드오프**: `AudioAnalyzer.analyze()`는 파일당 ~5초(librosa BPM/LUFS 계산이 대부분), `ScoreTranscriber`는 ~0.3-0.5초 — 전체 44개 실곡 배치 기준 파일당 평균 5.37초(2026-07-17 실측, `app/analyzers/audio.py`의 키 추정 벡터화 이후).

---

## 4. 알려진 버그 패턴 (2026-07-17 발견·수정)

| 증상 | 원인 | 해결 |
|---|---|---|
| 악보(MusicXML)가 실제 곡 길이보다 훨씬 일찍 끝남 | `ScoreTranscriber.MAX_EVENTS=96`이 문서화된 90초 분석 윈도우보다 먼저 이벤트 수집을 중단(44개 실곡 평균 33%만 커버) | `MAX_EVENTS` 상향 + 조기 `break` 제거 + 경고 문구를 실제 커버 구간으로 동적 표시. 재검증 평균 48.5%(90초 캡 산술과 일치) |
| Key 추정이 파일당 3초+ 소요 | `_estimate_key_np`가 전체 트랙 FFT 결과를 33만+ bin에 대해 순수 Python 루프로 순회 | `np.add.at` 벡터화 + `_frequency_bands_np`와 FFT 스펙트럼 공유(중복 계산 제거). 키/밴드/BPM 출력 완전 동일 확인, 9.46초→5.23초/파일 |

상세 근거: `music_insight_studio/docs/features/score_generation.md`의 "2026-07-17 Verification Fix" 절.

---

## 5. 테스트 전략

```powershell
cd music_insight_studio
.venv\Scripts\python.exe -m unittest discover -s tests   # 34 passed
```

- `tests/test_cli_mvp.py` 단일 파일 — 오디오 분석기, 스코어링, 악보 생성, 웹 서버 업로드 보안까지 커버
- 합성 fixture(`tests/fixtures/*.wav|mp3|flac`) + 실제 마스터링 완료곡(44개, 로컬 `Downloads/wav_마스터링/작업완료`)으로 이중 검증한 이력 있음(위 버그 2건 모두 실곡 배치 실행 중 발견)
- 네트워크 호출 없음(외부 API 미사용) — `librosa`/`basic-pitch` optional import는 로컬 패키지 유무 확인만

---

## 6. 확장 시 주의사항

- **새 분석 기준 추가**: `docs/*_criteria.md`에 문서화 후 `app/scoring/specialists.py`에 채점 로직 반영 — 문서 먼저, 코드는 그다음 원칙 유지.
- **악보 생성 정확도 개선**: `MAX_HEURISTIC_SECONDS`(현재 90초)를 늘리면 전곡 커버는 가능하나 동기 처리 시간이 곡 길이에 비례해 늘어남 — `docs/features/score_generation.md`가 이미 "백그라운드 잡으로 처리" 방향을 명시해뒀으니 그 결정을 뒤집지 말 것.
- **basic-pitch 설치**: 현재 미설치 상태에서만 검증됨(heuristic 폴백 경로). 설치 후 재검증 없이 "정확한 채보"라고 문서/UI에 표기하지 말 것.
- **다른 5개 프로젝트와 통합 금지**: 완전 독립 도구로 설계됨 — 파일 계약이나 공유 모듈을 만들지 말 것(`ARCHITECTURE.md`의 Dependency Boundary).

---

*Last Updated: 2026-07-17*

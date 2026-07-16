# Verification

## Verification Loop

Current phase: CLI MVP implementation and report verification.

Completion criteria:

- Required documents exist.
- Purpose, security boundary, acceptance criteria, verification commands, and HOLD conditions are documented.
- Reference-source reuse plan is documented.
- CLI MVP generates Markdown, Korean Markdown, and JSON reports.
- WAV, FLAC, and MP3 fixtures are analyzed through the same CLI path when codecs are available.
- Local Web MVP accepts an audio upload through `app.web.server` and writes the same report set through `AnalysisService`.
- Local Web MVP keeps the first screen to file upload, mode selection, and analyze action, then renders the Korean report inline.
- Korean report includes current Suno style and improved Suno style suggestions based on analysis evidence.
- Full-scale peaks must lower mix/master judgment to `수정 권장` and show headroom/clipping evidence.
- AI/Suno mode without prompt or lyrics must not be scored as release-ready AI naturalness.
- Korean report must show `우선 개선 포인트` before detailed technical sections.

## Design Verification Commands

```powershell
Get-ChildItem -Force .
Get-ChildItem -Force .\docs
Select-String -Path .\README.md -Pattern "목적"
Select-String -Path .\SPEC.md -Pattern "MVP Features"
Select-String -Path .\SECURITY_BOUNDARY.md -Pattern "Local-First Policy"
Select-String -Path .\ACCEPTANCE_CRITERIA.md -Pattern "MVP Completion Criteria"
Select-String -Path .\HOLD_CONDITIONS.md -Pattern "HOLD Conditions"
```

## Future Implementation Verification

```powershell
python -m pytest
python -m app.cli analyze .\tests\fixtures\sample.wav --out .\outputs
```

## Evidence Rule

Every verification step must use a real command or file read and must show a concrete pass/fail signal.

## Evaluation Criteria Verification

```powershell
Select-String -Path .\docs\evaluation_criteria.md -Pattern "Score Groups"
Select-String -Path .\docs\evaluation_criteria.md -Pattern "PASS / REVISE / HOLD"
Select-String -Path .\SPEC.md -Pattern "Evaluation Criteria Source"
```

## Specialist Criteria Verification

```powershell
Get-ChildItem -Force .\docs\*_criteria.md
Select-String -Path .\docs\composer_criteria.md -Pattern "Composer Criteria"
Select-String -Path .\docs\lyricist_criteria.md -Pattern "Lyricist Criteria"
Select-String -Path .\docs\producer_criteria.md -Pattern "Producer Criteria"
Select-String -Path .\docs\mixing_criteria.md -Pattern "Mixing Criteria"
Select-String -Path .\docs\mastering_criteria.md -Pattern "Mastering Criteria"
Select-String -Path .\docs\ai_music_criteria.md -Pattern "AI Music Criteria"
Select-String -Path .\docs\market_release_criteria.md -Pattern "Market and Release Criteria"
Select-String -Path .\docs\scoring_model.md -Pattern "Default Score Groups"
Select-String -Path .\docs\evaluation_criteria.md -Pattern "Specialist Criteria Documents"
```

## Docs Index Verification

```powershell
Select-String -Path .\docs\README.md -Pattern "Read Order"
Select-String -Path .\README.md -Pattern "문서 지도"
```

## CLI MVP Verification

```powershell
python -m unittest discover -s tests
python -m app.cli analyze .\tests\fixtures\sample.wav --out .\outputs --mode general
```

The unit tests generate their own temporary WAV fixture. The CLI command above requires a real fixture file if run manually.

## Optional DSP Verification

```powershell
python -c "import importlib.util as u; print('numpy', bool(u.find_spec('numpy'))); print('soundfile', bool(u.find_spec('soundfile'))); print('pyloudnorm', bool(u.find_spec('pyloudnorm')))"
python -m unittest discover -s tests
python -m app.cli analyze .\tests\fixtures\sample.wav --out .\outputs --mode general
```

If optional packages are absent, WAV fallback must still pass and MP3/FLAC must return a clear optional-dependency warning.


## Korean Report Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m compileall app tests
.\.venv\Scripts\python.exe -m app.cli analyze .\tests\fixtures\sample.wav --out .\outputs --mode general
Select-String -Path .\outputs\analysis_report.ko.md -Pattern "음악 분석 리포트|핵심 오디오 근거|세부 평가|기술적 오디오 품질"
```

Expected output files:

- `outputs/analysis_report.md`
- `outputs/analysis_report.ko.md`
- `outputs/analysis_report.json`
## Codec Format Verification

```powershell
.\.venv\Scripts\python.exe -c "import soundfile as sf; print(sf.__libsndfile_version__); print('MP3' in sf.available_formats()); print('FLAC' in sf.available_formats())"
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m app.cli analyze .\tests\fixtures\sample.wav --out .\outputs\wav --mode general
.\.venv\Scripts\python.exe -m app.cli analyze .\tests\fixtures\sample.flac --out .\outputs\flac --mode general
.\.venv\Scripts\python.exe -m app.cli analyze .\tests\fixtures\sample.mp3 --out .\outputs\mp3 --mode general
Select-String -Path .\outputs\wav\analysis_report.ko.md,.\outputs\flac\analysis_report.ko.md,.\outputs\mp3\analysis_report.ko.md -Pattern "BPM:|추정 Key:|LUFS:|주파수 밴드"
```

Expected current environment signal:

- libsndfile: `1.2.2`
- MP3 codec: `True`
- FLAC codec: `True`
- unittest: `33 tests OK`
- each short-fixture CLI run: `verdict=REVISE score=59.7` and four report files (Markdown, Korean Markdown, JSON, MusicXML)

## Scoring Calibration Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m app.cli analyze .\tests\fixtures\sample.wav --out .\outputs\calibrated_wav --mode general
Select-String -Path .\outputs\calibrated_wav\analysis_report.ko.md -Pattern "REVISE|duration_too_short_for_music_judgment|종합 점수"
```

Expected short-fixture signal:

- CLI verdict: `REVISE`
- score: around `59.7`
- evidence includes `duration_too_short_for_music_judgment`

## Release-Length Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m app.cli analyze .\tests\fixtures\release_90s.mp3 --out .\outputs\release_90s --mode general --target spotify
Select-String -Path .\outputs\release_90s\analysis_report.ko.md -Pattern "PASS|일반 발매 길이 구간|종합 점수|시장성"
```

Expected release-length fixture signal:

- CLI verdict: `PASS`
- score: around `72` (was `77` before section count became duration-proportional; see 2026-07-12 verification log entry)
- evidence includes `일반 발매 길이 구간`
- generated reports: Markdown, Korean Markdown, JSON, MusicXML

## Web MVP Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m compileall app tests
.\.venv\Scripts\python.exe -m app.web.server --host 127.0.0.1 --port 8765
```

Expected web signal:

- unittest includes Web MVP helper coverage.
- server prints `Music Insight Studio web UI: http://127.0.0.1:8765`.
- browser upload creates Markdown, Korean Markdown, and JSON reports under `outputs/web/<request-id>/`.
- result page renders Korean report content inline and shows only the JSON link.
- visible judgment labels are user-facing Korean labels such as `수정 권장`, not raw internal labels such as `REVISE / 수정 권장`.

## Simplified Web UI Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Expected simplified UI signal:

- Web form renders file upload and `mode`.
- Web form does not render `target`, `prompt`, or `lyrics` fields.
- Web upload helper returns Korean report text for inline rendering.

## Librosa BPM Provider Verification

```powershell
.\.venv\Scripts\python.exe -c "import importlib.util as u; print('librosa', bool(u.find_spec('librosa')))"
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Expected signal:

- `test_bpm_estimator_prefers_librosa_when_available` passes using a fake `librosa` module patched into `sys.modules` (unit-level, does not require a real install).
- If `librosa` is actually installed, `AudioAnalyzer._estimate_bpm_from_audio_np` calls `librosa.beat.beat_track` first and only falls back to the built-in spectral-flux estimator when `librosa` is missing, import fails, or returns confidence below `0.05`. Confirmed by direct comparison: a synthetic 120 BPM click track returns different BPM/confidence with `librosa` importable versus with its import blocked, showing both code paths actually execute (not just the mocked unit test).
- Real 38-file mastered WAV batch (local set, not in this repo): 0 errors, 15 unique BPM values, confidence 0.83-0.90 with `librosa==0.11.0` installed.

## Score Transcription Verification

```powershell
.\.venv\Scripts\python.exe -c "import importlib.util as u; print('basic_pitch', bool(u.find_spec('basic_pitch')))"
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Expected signal:

- `ScoreTranscriber` tries `basic-pitch` first, then a numpy/soundfile autocorrelation heuristic melody guide, then falls back to the section-energy chart if no pitched notes are reliable.
- `basic_pitch` is not installed in the current `.venv`; real-song CLI runs produce a MusicXML export containing `Heuristic melody guide` and the `transcription guide` limitation label, not `basic-pitch` note events.

## Result Link Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m app.web.server --host 127.0.0.1 --port 8765
```

Expected signal:

- `JSON` and `악보 MusicXML` both render as `<a ... target="_blank" rel="noopener">` in the result fragment; neither replaces the current tab.
- `악보 MusicXML` links to `/score?src=<url-encoded report path>`, a standalone page (`render_score_page`) that loads the vendored OSMD renderer and fetches/renders the MusicXML on page load, instead of an inline toggle panel on the result screen.
- `/score?src=` is validated by `parse_report_path` and returns `404` unless `src` resolves to a well-formed `/reports/<12-hex-id>/analysis_lead_sheet.musicxml` path. Confirmed live: `GET /score?src=/etc/passwd` -> `404`.
- Confirmed with a real browser session (Playwright): upload -> both links open in new tabs, original result screen stays intact, the score tab renders actual notation (SVG) with 0 console errors, and the malicious `src` request above returns `404` in the browser too.

## Suno Style Suggestion Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Expected style signal:

- Korean report includes `Suno 스타일 제안`.
- Korean report includes `현재 스타일` and `개선 스타일`.

## Verification Log

라운드별 검증 근거. `README.md`에 있던 로그를 이 문서로 옮겼다(2026-07-12) — README는 개요만, 상세 검증 이력은 여기.

| 날짜 | 내용 | 결과 |
|---|---|---|
| 2026-07-09 | 저장소에 커밋이 하나도 없던 상태 확인 — `.gitignore` 추가(`.venv/`, `__pycache__/`, `uploads/`, `outputs/`), 초기 커밋 생성 후 `origin/main` 푸시 | PASS: 53 files, `python -m unittest discover -s tests` 19/19 |
| 2026-07-09 | `requirements-optional.txt`가 `requirements.txt`와 완전 중복되던 것을 발견 — `ARCHITECTURE.md`에 명시된 실험용 의존성(librosa/demucs/pedalboard)만 남기도록 수정 | PASS: 19/19 유지 |
| 2026-07-09 | `VERIFICATION.md`의 "unittest: 11 tests OK"가 실제(19개)와 불일치 — 최신 값으로 갱신, 문서에 적힌 다른 기대 점수(REVISE 57.5, PASS 77)도 실제 CLI 실행으로 재확인 | PASS: 값 일치 확인 |
| 2026-07-09 | 웹 결과 화면에서 `` `code` ``/`**bold**` 인라인 마크다운이 그대로 문자로 노출되던 버그 발견(Suno 스타일 제안, 종합 점수/최종 판단, 기준 문서 참조 전부 영향) — `render_inline_markdown()` 추가로 수정, Playwright로 실제 브라우저 업로드까지 확인 | PASS: 19/19, 실브라우저 렌더링 확인 |
| 2026-07-09 | README/VERIFICATION.md/docs 2개 파일에 로컬 절대경로(사용자명 포함)가 그대로 커밋되어 있던 것 발견 — VERIFICATION.md의 검증 명령 ~22곳을 상대경로로, 참고 프로젝트 경로 언급은 이름만 남기고 경로 비공개로 수정 | PASS: 19/19, `grep -rl cs930` 추적 파일 0건 |
| 2026-07-09 | 실제 마스터링 완료 곡 38개 배치 분석 결과 전곡 REVISE·점수 4종에만 몰리는 현상 발견 — 원인 조사: (1) sample peak=1.000일 때 Mix/Master 점수를 고정 상한(65)으로 묶는 로직은 `test_full_scale_peak_is_flagged_and_not_overrewarded`로 이미 검증된 의도된 동작, (2) Composition/Production evidence가 실제 점수를 가른 신호(구간 에너지 편차)를 누락해 동일 evidence에서 다른 점수가 나오는 투명성 결함 발견 — `energy_label_variety`/`energy_spread` evidence 필드 추가로 수정 | PASS: 20/20 (신규 회귀 테스트 포함), mutation test로 수정 제거 시 신규 테스트 FAIL 확인 후 복원 재확인 |
| 2026-07-10 | 웹 UI에서 "분석하기" 클릭 후 분석이 끝나면 방금 고른 파일 선택이 초기화되는 문제 발견 — 원인: `<form method="post" action="/analyze">`가 매번 브라우저 전체 페이지를 새로 그리는 방식이라 `<input type="file">`이 항상 빈 상태로 재생성됨. `/analyze` 응답을 전체 페이지 대신 결과 조각(fragment)만 반환하도록 바꾸고, 클라이언트는 `fetch()` 기반 비동기 제출 + "분석 중..." 진행 표시로 전환(페이지 이동 없음) | PASS: 20/20 유지, curl로 `/analyze` 응답이 조각만 반환함을 확인, Playwright 실브라우저 테스트로 분석 완료 후에도 파일 선택(`sample_test.wav`)과 URL이 그대로 유지됨을 확인 |
| 2026-07-12 | 웹 UI에 MusicXML 악보를 브라우저에서 바로 렌더링하는 기능 추가(OpenSheetMusicDisplay 로컬 vendoring, "악보 MusicXML" 클릭 시에만 렌더링). 실브라우저 테스트에서 9마디가 한 줄에 겹쳐 보이는 문제 발견 — 원인: OSMD가 `EngravingRules.RenderXMeasuresPerLineAkaSystem` 미설정 시 전체 마디를 한 시스템에 욱여넣음. 설정 한 줄로 해결, 콘솔 에러 0건 확인. 이어서 실제 마스터링 완료곡 38개로 악보 자체가 빈약하다는 지적 재검증 — `AudioAnalyzer`의 구간 수가 곡 길이 무관하게 `total_sections = 8` 고정이던 것을 발견(38곡 전부 정확히 9마디, 5곡은 8구간 전부 "High energy" 동일 레이블). 곡 길이 비례(`TARGET_SECTION_SECONDS = 15`, 4~24 구간 클램프)로 변경 | PASS: 26/26(mutation test 2건 포함), 38곡 재분석 결과 마디 수 11~15로 곡 길이에 비례, 동일 레이블(변별력 0) 곡 5→2로 감소, `VERIFICATION.md` release_90s.mp3 기대 점수 77→72(재측정값)로 갱신 |
| 2026-07-12 | BPM 추정을 spectral-flux 온셋 기반으로 재작성(이전: coarse 그리드 락킹), 이어서 optional `librosa.beat.beat_track` provider를 최우선으로 추가. 별도로 `ScoreTranscriber`(`app/notation/transcription.py`) 신설 — optional `basic-pitch` 노트 이벤트 → 내장 numpy/soundfile 오토코릴레이션 멜로디 가이드 → 구간 에너지 차트 순 폴백. 웹 업로드에 확장자 화이트리스트 + 파일 시그니처 검증 + 용량 제한(`app/web/security.py`) 및 `/healthz`, 보안 응답 헤더 추가. 커밋 전 재검증 과정에서 이전 세션이 `ARCHITECTURE.md`에 적어 둔 "38곡 배치 고유 BPM 12→37개 증가"라는 수치가 실제 재실행 결과(15/38, 에러 0)와 불일치함을 발견해 문서를 실측값으로 정정 | PASS: 32/32(신규 6개 포함, `librosa`/보안/채보 커버), 38곡 실측 재검증(에러 0, 고유 BPM 15/38, 신뢰도 0.83-0.90), 실제 마스터링곡 1곡 CLI 전체 리포트(md/ko.md/json/musicxml) 생성 확인, `basic-pitch` 미설치 상태에서 heuristic 멜로디 가이드로 정상 폴백 확인 |
| 2026-07-12 | 결과 화면의 `JSON`/`악보 MusicXML` 링크 동작 불일치 지적 — JSON은 클릭 시 같은 탭이 그대로 이동(분석 결과 화면을 잃음), 악보 MusicXML은 같은 페이지 안에서 아래로 펼쳐짐. 두 링크 모두 새 탭(`target="_blank" rel="noopener"`)으로 통일 — 악보는 인라인 토글 대신 별도 `/score?src=` 페이지(`render_score_page`)에서 렌더링하도록 변경, `src` 파라미터는 기존 `/reports/` 경로 검증 로직을 `parse_report_path`로 공유 추출해 12자리 hex id + 허용된 파일명(`analysis_lead_sheet.musicxml`)만 통과하도록 검증 | PASS: 33/33(구식 인라인 토글 테스트 3개 교체, 신규 4개 추가), Playwright 실브라우저 검증 — 업로드 후 두 링크 모두 새 탭으로 열리고 원래 결과 화면 유지, 악보 탭에서 실제 SVG 표기 렌더링 + 콘솔 에러 0건, `/score?src=/etc/passwd` 직접 요청 시 404 확인 |
| 2026-07-12 | `requirements.txt`/`ARCHITECTURE.md`/`README.md` 3곳에서 여전히 librosa를 "사용 안 함/실험용"이라 적어놓은 게 바로 위 라운드에서 실제로 연결한 코드와 모순되는 것을 발견 — 정확한 서술로 수정하고, `requirements-optional.txt`를 tier 1(코드 연결됨: `librosa` 주석 해제, `basic-pitch`)/tier 2(코드 연결 없음: `music21`/`demucs`/`pedalboard`)로 재구성, `ARCHITECTURE.md` 폴더 구조 다이어그램에 실제 파일명(`transcription.py`, `security.py`) 명시 | PASS: 33/33, `pip install --dry-run -r requirements-optional.txt`로 구문 유효성 확인 |
| 2026-07-12 | 위 수정 직후 `ARCHITECTURE.md`의 "Actual Stack" 문장이 `pyloudnorm`을 `requirements-optional.txt` tier 1 항목 안에 넣어놓고 괄호로 "(requirements.txt)"라 적어 같은 문장 안에서 스스로 모순되는 것을 재발견 — 산문 대신 패키지별(파일 위치/있을 때/없을 때) 표로 교체, 아래 "Optional DSP Analysis Boundary" 섹션의 중복 서술은 표를 가리키도록 축소 | PASS: 문서만 변경, 코드 미변경이라 33/33 그대로 |
| 2026-07-12 | 자매 프로젝트 CareerDiff(문서만 있고 코드는 없는 상태)의 설계 방식과 비교 — module boundary(`app/web`은 `AnalysisService`만 호출, `app/scoring`은 `app.core`만 참조, `app/notation`은 `app.scoring` 미참조)가 CareerDiff의 `MODULE_BOUNDARIES.md`가 지향점으로만 적어둔 규칙과 이미 일치함을 import grep으로 직접 확인. 문서 쪽 격차만 최소 반영 — `docs/INDEX.md` 신규(루트 8개+`docs/` 전체 지도, 기존 `docs/README.md`는 평가기준만 다룸), `ARCHITECTURE.md`에 "Library Selection Policy" 절 추가(이미 실천 중이던 stdlib-fallback 우선 원칙 명문화). CareerDiff의 `docs/library-decisions/` 전체 폴더·`MODULE_BOUNDARIES.md` 단독 문서·RAG/threat-model/ops-runbook 계열은 이미 구현된 단일 워크플로우 로컬 MVP 규모에 과하다고 판단해 미적용 | PASS: 33/33, `docs/INDEX.md`가 참조하는 파일 전부 존재 확인(`[ -f ]` 체크, 누락 0건) |
| 2026-07-15 | 위 33/33 로그 이후 어느 시점에 커밋된 `818f3b2`(librosa/basic-pitch optional providers 추가)에서 `app/analyzers/audio.py`의 `_analyze_wav_fallback`(stdlib-only, numpy 없는 경로)에 numpy 전용 함수 `_estimate_bpm_from_audio_np(y, ..., np)` 호출이 잘못 섞여 들어가 있던 것을 발견 — `y`/`np` 둘 다 이 경로엔 정의되지 않아 `NameError`. 이 라운드가 33/33으로 기록된 이유는 그 시점 로컬 venv에 numpy가 설치돼 있어 numpy-fallback 경로(`_analyze_wav_fallback`)가 테스트로 한 번도 실제 실행되지 않았기 때문으로 추정(환경 의존적 커버리지 공백). 수정: 해당 줄 삭제(반환값도 애초에 미사용이던 죽은 코드였음, BPM은 폴백 경로에서 원래도 "unestimated"로 남는 게 의도된 동작). `_has_optional_dsp`를 `unittest.mock.patch`로 강제 `False`로 만들어 numpy 설치 여부와 무관하게 이 경로를 항상 실행하는 회귀 테스트(`test_stdlib_wav_fallback_runs_without_numpy_available`) 추가 — 환경 의존적 커버리지 공백 자체를 구조적으로 제거 | PASS: 30/30(4 skipped, 신규 1개 포함), mutation test로 수정 제거 시 신규 테스트가 정확히 같은 `NameError`로 FAIL함을 확인 후 복원 재확인 |



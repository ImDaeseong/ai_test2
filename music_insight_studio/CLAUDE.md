# CLAUDE.md — music_insight_studio

> 음원 파일과 Suno 등 AI 음악 제작 자료를 분석해 한국어 리포트(Markdown/JSON/MusicXML)를 생성하는 로컬 우선 음악 분석 도구.
> BPM, Key, 믹싱 상태, AI 음악 자연스러움, 시장성을 분석한다. CLI와 로컬 Web UI(8765) 두 가지 진입점을 제공한다.

---

## 절대 규칙

- **로컬 우선**: 오디오 파일·프롬프트·리포트를 외부 서비스로 전송하지 않는다 (사용자가 명시적으로 통합을 켜지 않는 한). 상세: `SECURITY_BOUNDARY.md`
- **비밀값 저장 금지**: API 키, 토큰, 비밀번호, 사내 비공개 정보를 저장하지 않는다.
- **파일 경로 검증**: 업로드 파일명을 안전하게 정규화하고 `..`·절대 경로 삽입·무관한 파일 덮어쓰기를 막는다. 임시 입력은 `uploads/`, 생성 결과는 `outputs/`에만 둔다.
- **아티스트 복제 금지**: 특정 생존 아티스트의 목소리·스타일을 복제하거나 사칭하도록 유도하지 않는다. 유사성은 상위 수준 참고 표현으로만 제시한다.
- **플랫폼 성과 보장 금지**: 스트리밍·매출 성과를 약속하지 않는다.
- **HOLD 조건은 `HOLD_CONDITIONS.md`를 따른다** — 외부 API 통합 추가, 자동 업로드/퍼블리싱 추가, 유료 모델 의존성 추가, 업로드 파일 장기 보관, 저작권 있는 참조 오디오와의 비교는 사람 검토 전까지 진행하지 않는다.

## 파일 역할

| 경로 | 역할 | 수정 시 주의사항 |
|---|---|---|
| `app/analyzers/audio.py`, `text.py` | 오디오/텍스트 분석 (BPM, Key, LUFS 등) | `librosa`/`basic-pitch` 미설치 시 내장 폴백 자동 사용 |
| `app/scoring/` | 채점 엔진·루브릭·전문 평가(specialists) | 점수 분포 변경 시 회귀 테스트 필수 |
| `app/notation/` | MusicXML 세션 악보 생성 | 채보(transcription) 로직 포함 |
| `app/reports/` | Markdown/한국어 Markdown/JSON 리포트 생성 | 출력 포맷 변경 시 3개 리포터 모두 동기화 |
| `app/cli/__main__.py` | CLI 진입점 (`analyze` 명령) | |
| `app/web/server.py`, `security.py` | 로컬 Web UI (stdlib `http.server`, Flask/FastAPI 미사용) | 업로드 경로 검증은 `security.py` |
| `app/services/analysis_service.py` | CLI/Web 공통 분석 오케스트레이션 | |
| `tests/fixtures/` | 합성·실제 오디오 fixture (mp3/wav/flac) | |
| `requirements.txt` / `requirements-optional.txt` | 필수(numpy/soundfile/pyloudnorm) / 선택(librosa/basic-pitch) 의존성 | 선택 의존성 없어도 폴백으로 동작해야 함 |

---

## 검증 명령어

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests
# 목표: 34개 테스트 전체 통과 (선택 의존성 librosa/basic-pitch 미설치 환경에서는 일부 스킵될 수 있음 —
# 2026-08-17 이 .venv에서는 34 passed, 0 skipped 확인)
```

## 완료 기준

`tests/` 전체 통과(스킵 제외). CLI(`python -m app.cli analyze ...`)와 Web(`python -m app.web.server`) 둘 다 `tests/fixtures/sample.wav`로 리포트 4종(md/ko.md/json/musicxml) 정상 생성.

---

## 변경 전 확인 문서

이 프로젝트는 `ai_test2` 루트 문서 대신 자체 governance 문서 세트를 갖고 있다 (`ai_test3`에서 이전, 2026-07-17). 구조 변경 전에는 다음을 먼저 확인한다: `SPEC.md` → `ARCHITECTURE.md` → `SECURITY_BOUNDARY.md` → `HOLD_CONDITIONS.md` → `VERIFICATION.md` → `ROADMAP.md`. 전체 문서 지도는 `docs/INDEX.md`.

*Last Updated: 2026-08-17*

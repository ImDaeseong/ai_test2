# Music Insight Studio

음원 파일과 Suno 등 AI 음악 제작 자료를 분석해 한국어 리포트를 생성하는 로컬 우선 음악 분석 도구.

## 정의

- **목적**: 나는 음악 제작/발매 준비 상황에서 이 도구로 음원 파일을 업로드해서 BPM, Key, 믹싱 상태, AI 음악 자연스러움, 시장성을 분석한 한국어 리포트를 얻는다.
- **입력**: MP3 / WAV / FLAC (필수), Suno 프롬프트·가사·장르·목표 플랫폼 (선택, CLI만 지원)
- **출력**: Markdown, 한국어 Markdown, JSON, MusicXML 세션 차트
- **상태**: CLI MVP + 로컬 Web MVP 구현·검증 완료, 단위 테스트 33개 통과
- **비목표**: 특정 가수 복제, 외부 플랫폼 자동 업로드, 스트리밍 성과 보장, 완전한 음악학적 채보/전문 마스터링 대체

## 스택

| 구분 | 내용 |
|---|---|
| 언어/런타임 | Python, stdlib `http.server` (Flask/FastAPI 미사용) |
| 필수 의존성 | `numpy`, `soundfile`, `pyloudnorm` (`requirements.txt`) |
| 선택 의존성 | `librosa`(BPM 추정 1순위 provider), `basic-pitch`(악보 채보 1순위 provider) — 둘 다 미설치 시 내장 폴백 자동 사용. 상세: `ARCHITECTURE.md` "Dependency Table" |
| 참조 소스 | `Analysis_music`, `mp3_daw` (이 저장소 밖 로컬 프로젝트, 상세: `docs/reference_sources.md`) |

## 시작하기

```powershell
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
```

더블클릭으로 Web UI를 바로 열려면 `run.bat` 실행 (`.venv` 필요). `numpy`/`soundfile`/`pyloudnorm` 미설치 시 WAV 전용 stdlib 폴백으로 동작.

## 사용법

**CLI**

```powershell
.\.venv\Scripts\python.exe -m app.cli analyze .\tests\fixtures\sample.wav --out .\outputs --mode general
```

생성물: `analysis_report.md`(영문), `analysis_report.ko.md`(한국어), `analysis_report.json`(구조화 데이터), `analysis_lead_sheet.musicxml`(세션 악보).

**Web**

```powershell
.\.venv\Scripts\python.exe -m app.web.server --host 127.0.0.1 --port 8765
```

`http://127.0.0.1:8765`에서 파일 업로드 → 분석 모드 선택 → 같은 화면에 한국어 리포트 표시(페이지 이동 없음). `JSON`/`악보 MusicXML` 링크는 둘 다 새 탭에서 열림.

## 문서 지도

| 문서 | 용도 |
|---|---|
| `docs/INDEX.md` | 전체 문서 지도(루트 8개 + `docs/` 전체) |
| `SPEC.md` | 제품 범위, 입출력, MVP 기능 목록 |
| `ARCHITECTURE.md` | 기술 스택, 의존성, 모듈 경계, 데이터 흐름 |
| `SECURITY_BOUNDARY.md` / `HOLD_CONDITIONS.md` | 보안 경계 / 구현 중단 조건 |
| `ACCEPTANCE_CRITERIA.md` / `ROADMAP.md` | 완료 기준 / 단계별(Phase 0-7) 진행 상태 |
| `VERIFICATION.md` | 검증 명령, 기대 결과, 라운드별 Verification Log |
| `docs/README.md` | 평가 기준 문서(작곡/작사/프로듀싱/믹싱/마스터링 등) 읽는 순서 |
| `docs/commercial/` | 상용화 전환 시 확인할 문서 — 현재 공개 출시는 HOLD |

## 개발 원칙

코드보다 문서(SPEC/ARCHITECTURE/ACCEPTANCE_CRITERIA/SECURITY_BOUNDARY/HOLD_CONDITIONS)를 먼저 정의하고, 검증이 끝난 단위로 작게 커밋한다. 이 프로젝트가 실제로 보여주는 역량:

- **검증 루프**: 수정마다 회귀 테스트 추가 + mutation test(수정을 되돌렸을 때 테스트가 실제로 실패하는지 확인) 후 복원·커밋
- **보안 감각**: 커밋된 문서의 로컬 절대경로(사용자명 포함) 노출을 직접 찾아 제거
- **실데이터 검증**: 합성 fixture뿐 아니라 실제 마스터링 완료곡 38개 배치 분석으로 점수 분포 이상을 발견·수정

라운드별 근거는 `VERIFICATION.md`의 Verification Log 참고.

# CLAUDE.md — ai_test2

AI 음악 비디오 프롬프트 생성, 애니메이션, CapCut 편집 자동화, 유튜브 리서치, 음악 분석, 채용 적합도 분석 프로젝트 모음.

## 저장소 목적

나는 **Suno 음원**에서 시작해 **AI 이미지·영상 프롬프트 생성 → CapCut 편집 드래프트 자동 생성** 흐름을 자동화하기 위해 이 저장소를 사용한다.

## 변경 전 확인 문서

구조 변경, 리팩터링, 신규 기능, 공개 배포 준비를 시작하기 전에는 루트 문서를 먼저 확인한다.

1. `SPEC.md` — 목적, 범위, 완료 기준
2. `ARCHITECTURE.md` — 현재 구조 위험, 목표 모듈 경계, 파일 계약
3. `SECURITY_BOUNDARY.md` — API 키, 미디어, 유튜브 수집, 프롬프트 안전 경계
4. `HOLD_CONDITIONS.md` — 중단하고 사람 검토가 필요한 조건
5. `VERIFICATION.md` — 진행률 게이트와 검증 명령
6. `ROADMAP.md` — 현대화 순서

## 6개 프로젝트 구조

```
[1] ai_img_video_aiBoygirl
      └─ 09_video_motion_prompts.md 생성 (CapCut Editing Map 포함)
            ↓
[2] ai_img_video_prompt_capcut
      + Suno 음원(.wav) + LRC + Kling 생성 클립(.mp4)
            ↓
      timeline.json + shot_list.md + CapCut 드래프트 자동 생성

[3] ai_anime
      └─ 곡당 5파일 생성 (캐릭터 시트, 이미지, 영상 프롬프트, 제작 가이드)

[4] youtube_research
      └─ 독립 실행 — AI 음악 채널 벤치마킹 (yt-dlp 기반, API 키 불필요)

[5] music_insight_studio
      └─ 독립 실행 — 로컬 음악 분석(BPM/Key/LUFS/믹싱·마스터링 평가), 외부 API 불필요
      └─ ai_test3에서 이동 (2026-07-17) — 다른 4개와 파일/의존성 공유 없음

[6] CareerDiff
      └─ 독립 실행 — 채용공고·이력서 적합도 분석, 키가 있으면 OpenAI 사용
      └─ 기본 mock 경로와 런타임 개인 데이터는 다른 5개 프로젝트와 공유하지 않음
```

## 핵심 규칙

- 비밀값(.env, API 키, 토큰)을 코드나 저장소에 포함하지 않는다.
- `.env.example`에 변수명과 설명만 기재한다. 실제 값은 `.env`(gitignore)에만.
- 각 프로젝트는 독립 실행 가능해야 한다 — 다른 프로젝트 파일을 직접 import하지 않는다.
- 새 프로젝트 추가 시 이 파일과 README.md 동시 업데이트.

## 보안 경계

- 음악·영상 도구 5개는 로컬 처리만 수행한다. CareerDiff는 앱 환경변수나 Git 제외 개인 공유 파일의 OPENAI_API_KEY를 선택적으로 사용하며 외부 전송 고지가 필요하다.
- yt-dlp: 공개 메타데이터만 수집, 음원 다운로드 없음
- music_insight_studio: numpy/soundfile/librosa/pyloudnorm/basic-pitch 전부 로컬 패키지, 네트워크 호출 없음

## 검증 명령

```powershell
cd ai_anime                      ; python -m pytest tests_unit.py -q
cd ../ai_img_video_aiBoygirl     ; python -m pytest -q
cd ../ai_img_video_prompt_capcut ; python -m pytest tests_unit.py -q
cd ../youtube_research           ; python -m pytest tests_unit.py -q
cd ../music_insight_studio       ; .venv\Scripts\python.exe -m unittest discover -s tests
cd ../CareerDiff/app             ; npm run typecheck ; npm test ; npm run lint
cd ../..                         ; python -m unittest tests.test_repository_contract
```

## HOLD 조건 (배포 전 필수)

- [ ] 각 프로젝트 테스트 전량 PASS
- [ ] .env 파일이 git에 포함되지 않음 확인


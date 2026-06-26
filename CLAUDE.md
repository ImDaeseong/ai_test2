# CLAUDE.md — ai_test2

AI 음악 비디오 프롬프트 생성, 애니메이션, CapCut 편집 자동화, 멀티 에이전트 실행, 유튜브 리서치 도구 모음.

## 저장소 목적

나는 **Suno 음원**에서 시작해 **AI 이미지·영상 프롬프트 생성 → CapCut 편집 드래프트 자동 생성** 흐름을 자동화하기 위해 이 저장소를 사용한다.

## 5개 프로젝트 의존성 순서

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
      └─ ai_multi_agent 웹 UI로 실행 가능

[4] ai_multi_agent
      └─ [1][3] 생성 프롬프트를 OpenRouter API로 실행
      └─ 5개 웹 UI (포트 5200/5300/5400/5500/5600)

[5] youtube_research
      └─ 독립 실행 — AI 음악 채널 벤치마킹 (yt-dlp 기반, API 키 불필요)
```

## 핵심 규칙

- 비밀값(.env, API 키, 토큰)을 코드나 저장소에 포함하지 않는다.
- `.env.example`에 변수명과 설명만 기재한다. 실제 값은 `.env`(gitignore)에만.
- 각 프로젝트는 독립 실행 가능해야 한다 — 다른 프로젝트 파일을 직접 import하지 않는다.
- 새 프로젝트 추가 시 이 파일과 README.md 동시 업데이트.

## 보안 경계

- 외부 API: ai_multi_agent만 OpenRouter 사용 (OPENROUTER_API_KEY 필요)
- 나머지 4개 프로젝트: 외부 API 없음, 로컬 파일 처리만
- yt-dlp: 공개 메타데이터만 수집, 음원 다운로드 없음

## 검증 명령

```powershell
cd ai_anime                      ; python -m pytest tests_unit.py -q
cd ../ai_img_video_aiBoygirl     ; python -m pytest -q
cd ../ai_img_video_prompt_capcut ; python -m pytest tests_unit.py -q
cd ../ai_multi_agent             ; python -m pytest tests_unit.py -q
cd ../youtube_research           ; python -m pytest tests_unit.py -q
```

## HOLD 조건 (배포 전 필수)

- [ ] 각 프로젝트 테스트 전량 PASS
- [ ] .env 파일이 git에 포함되지 않음 확인
- [ ] ai_multi_agent: `.env.example` → `.env` 복사 후 API 키 입력 검증

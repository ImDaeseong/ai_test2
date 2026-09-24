# ai-tools

**🤔 [쉬운 설명 보기](https://htmlpreview.github.io/?https://github.com/ImDaeseong/ai_test2/blob/main/ELI5.html)** — 비개발자를 위한 한 페이지 요약

AI 뮤직비디오 제작, 프롬프트 생성, YouTube 조사, 로컬 음악 분석, 채용 적합도 분석을 위한 6개 독립 프로젝트 모음입니다. 각 프로젝트의 상세 옵션과 입력 형식은 해당 폴더의 `README.md`를 확인하세요.

## 사전 요구사항

- Windows PowerShell
- Python 3.11 권장 (`ai_anime`과 `ai_img_video_aiBoygirl`은 3.9+)
- Node.js와 npm (`CareerDiff`만 사용)
- CapCut PC, Suno 음원, LRC 가사, Kling 영상 클립은 CapCut 파이프라인을 실제로 사용할 때만 필요

## 환경 설정

저장소를 받은 뒤 사용할 프로젝트 폴더마다 가상환경과 의존성을 별도로 설치합니다.

```powershell
cd C:\path\to\ai_test2\<프로젝트>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

프로젝트별 추가 설치:

| 프로젝트 | 설치 명령 |
|---|---|
| `ai_anime` | `python -m pip install -r requirements.txt` |
| `ai_img_video_aiBoygirl` | 실행 의존성 없음 · 테스트 시 `python -m pip install -r requirements-dev.txt` |
| `ai_img_video_prompt_capcut` | `python -m pip install click mutagen pytest` |
| `youtube_research` | `python -m pip install yt-dlp pytest` |
| `music_insight_studio` | `python -m pip install -r requirements.txt` · 정확도 향상 시 `python -m pip install -r requirements-optional.txt` |
| `CareerDiff` | `cd CareerDiff\app; npm install` |

### API 키

외부 API 키가 필요한 프로젝트만 예제 파일을 복사해 설정합니다. 실제 키가 든 `.env`와 `.env.local`은 Git에 포함하지 않습니다.

```powershell
# CareerDiff: 선택 사항이며, 미설정 시 결정론적 로컬 분석기 사용
Copy-Item CareerDiff\app\.env.example CareerDiff\app\.env.local
```

| 프로젝트 | 환경변수 |
|---|---|
| `CareerDiff` | `OPENAI_API_KEY`, `OPENAI_MODEL` 모두 선택. 앱 환경변수에 키가 없으면 Git에서 제외된 `../ai_agent/keyinfo/keys.env`의 `OPENAI_API_KEY`를 서버에서만 읽음 |

`CareerDiff`가 OpenAI 모드이면 분석 전에 외부 전송 안내와 동의 체크를 표시합니다. 동의하지 않은 요청은 서버에서도 거부되며, 키가 없으면 입력을 외부로 보내지 않는 로컬 분석기를 사용합니다.

## 프로젝트와 실행 방법

| 프로젝트 | 용도 | 실행 |
|---|---|---|
| [`ai_anime`](./ai_anime/) | 곡별 애니메 캐릭터·이미지·영상 프롬프트 생성 | `python main.py create-all --force` |
| [`ai_img_video_aiBoygirl`](./ai_img_video_aiBoygirl/) | 고정 AI Boy/Girl 캐릭터 MV 프롬프트 생성 | `python main.py create-all --input-dir input --force` |
| [`ai_img_video_prompt_capcut`](./ai_img_video_prompt_capcut/) | 음원·LRC·Kling 클립으로 CapCut 타임라인과 드래프트 생성 | `python main.py build --song "곡명"` |
| [`youtube_research`](./youtube_research/) | 공개 YouTube 메타데이터 수집과 벤치마킹 리포트 | `python run.py search 30` 또는 `run.bat` |
| [`music_insight_studio`](./music_insight_studio/) | 로컬 음원의 BPM·Key·LUFS·믹싱 상태 분석 | `python -m app.web.server --host 127.0.0.1 --port 8765` |
| [`CareerDiff`](./CareerDiff/docs/README.md) | 채용공고와 이력서의 적합도 분석 | `cd CareerDiff\app; npm run dev` |

## MV 제작 흐름

```text
ai_img_video_aiBoygirl
  → 09_video_motion_prompts.md 생성
  → ai_img_video_prompt_capcut에 Suno 음원(.wav), 가사(.lrc), Kling 클립(.mp4) 입력
  → timeline.json, shot_list.md, CapCut 드래프트 생성
```

`ai_anime`, `youtube_research`, `music_insight_studio`, `CareerDiff`는 위 흐름과 독립적으로 실행됩니다.

## 검증

각 명령은 해당 프로젝트 폴더에서 실행합니다.

```powershell
# Python 프로젝트
python -m pytest tests_unit.py -q       # ai_anime, ai_img_video_prompt_capcut, youtube_research
python -m pytest -q                     # ai_img_video_aiBoygirl
python -m unittest discover -s tests    # music_insight_studio

# CareerDiff
cd CareerDiff\app
npm test
npm run typecheck
npm run lint
```

## 저장소 문서

- [`SPEC.md`](./SPEC.md): 전체 범위와 완료 기준
- [`ARCHITECTURE.md`](./ARCHITECTURE.md): 프로젝트 구조와 파일 계약
- [`SECURITY_BOUNDARY.md`](./SECURITY_BOUNDARY.md): API 키·미디어·외부 데이터 보안 경계
- [`HOLD_CONDITIONS.md`](./HOLD_CONDITIONS.md): 사람 검토가 필요한 중단 조건
- [`VERIFICATION.md`](./VERIFICATION.md): 상세 검증 명령과 이력
- [`ROADMAP.md`](./ROADMAP.md): 개선 순서

생성 결과와 개인 입력 데이터는 프로젝트별 `output/`, `outputs/`, `uploads/`, `CareerDiff/data/`에 저장될 수 있습니다. 커밋 전 비밀값과 개인 데이터가 포함되지 않았는지 확인하세요.
# Source-only public release

This repository distributes source code only. Images, audio, video, and
compiled executables are excluded. Supply your own files in the input,
reference, assets, or static directories described by each subproject before
running workflows that require them. A fresh clone contains no example media;
some demonstrations and documented commands need local media to run.
Run `python scripts/check_source_only.py` before committing.

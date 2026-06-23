# ai_multi_agent 목적 및 개선 기준

작성 기준일: 2026-06-01

이 문서는 `ai_multi_agent` 소스 개선의 기준 문서입니다. 이후 구현은 이 목적을 우선합니다.

## 1. 최종 역할 정의

`ai_multi_agent`는 새 프롬프트를 대량으로 다시 만드는 도구가 아니라, 기존 프로젝트 결과를 실제 제작에 쓰기 좋게 연결하는 작업 관리자입니다.

폴더 구조는 `ai_multi_agent`가 `ai_img_video_prompt`, `ai_story`, `ai_Scenario`와 같은 부모 폴더 아래에 있는 형태를 기준으로 유지한다. 내부 참조는 특정 드라이브의 절대 경로에 의존하지 않고, `ai_multi_agent`의 부모 폴더를 workspace root로 계산해 상대적으로 찾는다.

연결 대상:

- `ai_img_video_prompt`: 곡별 MV 이미지/비디오 프롬프트 패키지
- `ai_story`: 챕터 단위 소설 제작 프롬프트와 결과
- `ai_Scenario`: 씬 단위 시나리오 제작 프롬프트와 결과

핵심 역할:

- 곡명 또는 작품명을 선택한다.
- 현재 필요한 다음 작업만 보여준다.
- 생성 제한을 고려해 한 번에 하나씩 진행한다.
- 생성물과 프롬프트를 같은 제작 단위 폴더에 묶는다.
- 진행 상태를 저장하고 이어서 작업할 수 있게 한다.

## 2. MV 이미지/비디오 제작 관리자

### 배경

`ai_img_video_prompt`는 이미 곡별로 다음 파일을 생성한다.

```text
00_prompt_overview.md
01_master_style_prompt.md
02_style_lock_prompt.md
03_vocal_image_prompt.md
04_guitar_image_prompt.md
05_bass_image_prompt.md
06_drum_image_prompt.md
07_stage_image_prompt.md
08_crowd_image_prompt.md
09_video_motion_prompts.md
```

따라서 `ai_multi_agent`의 1차 역할은 곡을 재분석하는 것이 아니라, 이 결과를 기반으로 실제 이미지 생성을 한 장씩 진행하게 하는 것이다.

### 목표 흐름

```text
곡명 선택
→ ai_img_video_prompt/output/곡명 읽기
→ 파트별 작업 폴더 생성
→ 다음 미생성 이미지 프롬프트 1개 실행
→ 이미지 1장 생성 후 image.png 저장
→ 해당 이미지 기준 비디오 프롬프트와 함께 묶기
→ 다음 파트로 이동
```

### 파트 기준

- `01_vocal`: `03_vocal_image_prompt.md`
- `02_guitar`: `04_guitar_image_prompt.md`
- `03_bass`: `05_bass_image_prompt.md`
- `04_drum`: `06_drum_image_prompt.md`
- `05_stage`: `07_stage_image_prompt.md`
- `06_crowd`: `08_crowd_image_prompt.md`

각 파트 폴더에는 다음 파일을 둔다.

```text
image_prompt.md
video_prompt.md
image.png
manifest.json
status.json
```

`video_prompt.md`는 `09_video_motion_prompts.md` 전체를 그대로 복사하는 것보다, 해당 파트의 이미지와 연결해 사용할 수 있도록 필요한 비디오 지시를 조합하는 방향을 우선한다.

### 생성 제한

이미지 생성은 무한대로 자동 실행하지 않는다.

- 한 번에 한 장만 진행한다.
- 다음 작업 하나만 안내한다.
- 생성 완료 여부는 파일 존재 또는 상태 파일로 판단한다.
- 사용자가 중단해도 다음 실행에서 이어간다.

## 3. Story/Scenario 제작 관리자

### ai_story 결과 사용 방식

`ai_story`는 소설 산문용 챕터 제작 엔진이다.

기본 구조:

```text
ai_story/output/작품명/
  state.json
  설정집.md
  START_PROMPT.md
  chapters/
    ch01_GPT_프롬프트.md
    ch02_GPT_프롬프트.md
```

`ai_multi_agent`는 작품명을 선택하면 `state.json`과 `chapters` 폴더를 읽고 다음 미완료 챕터를 안내하거나 실행한다.

목표 흐름:

```text
소설 제목 선택
→ 다음 chXX_GPT_프롬프트.md 확인
→ API 자동 실행 또는 GPT Plus 수동 실행용 프롬프트 제공
→ GPT 결과를 ai_multi_agent/output/story/작품명/chapters/chXX_GPT_출력.md로 저장
→ Claude 마무리 단계 안내 또는 API 실행
→ chXX_완성.md 저장
→ story.py save XX 흐름으로 상태 갱신
```

### ai_Scenario 결과 사용 방식

`ai_Scenario`는 시나리오/각본용 씬 제작 엔진이다.

기본 구조:

```text
ai_Scenario/output/작품명/
  state.json
  설정집.md
  START_PROMPT.md
  scenes/
    씬001_GPT_프롬프트.md
    씬002_GPT_프롬프트.md
```

목표 흐름:

```text
시나리오 제목 선택
→ 다음 씬XXX_GPT_프롬프트.md 확인
→ API 자동 실행 또는 GPT Plus 수동 실행용 프롬프트 제공
→ GPT 결과를 ai_multi_agent/output/scenario/작품명/scenes/씬XXX_GPT_출력.md로 저장
→ Claude 마무리 단계 안내 또는 API 실행
→ 씬XXX_완성.md 저장
→ scenario.py save XXX 흐름으로 상태 갱신
```

## 4. API 모드와 수동 모드

### API 모드

OpenRouter API 키가 있는 경우:

- 프롬프트를 API로 전송한다.
- 결과를 ai_multi_agent/output 아래의 용도별 폴더에 별도 저장한다.
- 실패 시 상태 파일에 실패 원인을 남긴다.
- 사용자가 재시도할 수 있게 한다.

### 수동 모드

GPT Plus만 사용하는 경우:

- 로컬 코드가 ChatGPT 웹을 자동 조작하지 않는다.
- 다음 프롬프트를 파일과 콘솔에 제공한다.
- 사용자가 결과를 붙여넣거나 파일로 저장하면 agent가 다음 단계로 넘긴다.

## 5. 상태 관리

각 작업 루트에는 상태 파일을 둔다.

MV 예:

```json
{
  "mode": "mv",
  "source": "ai_img_video_prompt",
  "title": "그래도 와줘",
  "current_part": "01_vocal",
  "parts": {
    "01_vocal": {
      "image_prompt": "ready",
      "image": "missing",
      "video_prompt": "ready"
    }
  }
}
```

Story/Scenario 예:

```json
{
  "mode": "story",
  "title": "두번째봄",
  "current_unit": 1,
  "unit_label": "ch01",
  "gpt_output": "missing",
  "final_output": "missing"
}
```

상태 파일은 중단/재개, 다음 작업 찾기, 완료율 표시의 기준이 된다.

## 6. 우선 구현 순서

1. MV 곡 목록 표시
2. 곡 선택 후 파트별 작업 폴더 생성
3. 다음 미완료 이미지 프롬프트 1개 표시
4. 이미지 등록 및 상태 갱신
5. 파트별 비디오 프롬프트 묶기
6. MV 진행률 표시
7. `ai_story` 작품 목록 및 다음 챕터 안내
8. `ai_Scenario` 작품 목록 및 다음 씬 안내
9. API 자동 실행 모드 추가
10. Reviewer/재분석 보조 기능 추가

## 7. 기존 Agent 역할의 재정의

기존 구조의 `ScriptAgent`, `ImageAgent`, `VideoAgent`, `ReviewerAgent`는 완전히 폐기하지 않는다. 다만 기본 경로에서는 재생성보다 진행 관리가 우선이다.

- `ScriptAgent`: 기존 결과를 읽고 제작 단위로 분해하는 역할로 전환
- `ImageAgent`: 다음 이미지 1장 생성 프롬프트 제공/등록 관리
- `VideoAgent`: 생성 이미지와 연결할 비디오 프롬프트 패키징
- `ReviewerAgent`: 누락, 파일명, placeholder, 품질 보정 필요 여부 확인

재분석은 실패 복구나 품질 개선이 필요할 때의 보조 기능으로 둔다.

# STORY_ANALYZER_SPEC.md
# 가사 기반 스토리 분석 엔진 설계 문서

작성일: 2026-06-13  
대상 프로젝트: ai_img_video_aiBoygirl  
목적: 공연 MV 생성기 → 가사 기반 스토리 MV 생성기로 확장

---

## 1. 문제 정의

### 현재 파이프라인

```
input/*.txt
  ↓ parse_song()      ← 장르·BPM·무드·감정만 추출
  ↓ infer_profile()   ← genre_profiles.json 키워드 매칭
  ↓ 공연 프롬프트 생성  ← vocal/guitar/bass/drum/stage/atmosphere
  ↓ 이미지 생성 → 영상
```

### 현재 시스템이 생성하는 MV

- 보컬 클로즈업
- 기타/베이스/드럼 연주
- 무대 전경
- 분위기/실루엣

### 실제 뮤직비디오가 필요한 것

```
가사: "오늘도 같은 전철, 너는 내 옆에 있었지"
현재: 보컬이 무대에서 노래하는 공연 컷
목표: 퇴근 전철 안, 주인공이 그녀를 발견, 말 못 하고 문이 닫힘
```

### 핵심 결함

가사에서 **누가 / 어디서 / 언제 / 무엇을 / 왜** 를 추출하는 엔진이 없다.

---

## 2. 목표

| 단계 | 목표 |
|------|------|
| Phase 1 | 가사 → `story_metadata.json` 생성 (`story_analyzer.py`) |
| Phase 2 | `story_metadata.json` → story_scene 프롬프트 생성 |
| Phase 3 | `main.py` 파이프라인에 통합 |

**완성 후 파이프라인:**

```
input/*.txt
  ↓ parse_song()           ← 기존 유지
  ↓ story_analyzer.py      ← 신규 추가
  ↓ story_metadata.json    ← 신규 산출물
  ↓ 프롬프트 생성 (기존 + story_scene 추가)
  ↓ 이미지 → 영상
```

---

## 3. story_metadata.json 스키마

### 3.1 최상위 구조

```json
{
  "song_title": "string",
  "core_emotion": "string",
  "story_theme": "string",
  "characters": ["string"],
  "main_location": "string (영어)",
  "symbols": ["string (영어)"],
  "story_arc": { ... },
  "scenes": [ ... ],
  "_meta": { ... }
}
```

### 3.2 story_arc (섹션별 서사)

```json
"story_arc": {
  "intro":         "string — 시작 상황",
  "verse":         "string — 관계 발전 또는 현재 상황",
  "pre_chorus":    "string — 긴장 고조",
  "chorus":        "string — 감정 폭발 또는 클라이맥스",
  "bridge":        "string — 갈등 또는 전환",
  "final_chorus":  "string — 해결 또는 여운",
  "outro":         "string — 마무리"
}
```

- 해당 섹션이 가사에 없으면 `null`

### 3.3 scenes (장면 목록)

```json
"scenes": [
  {
    "scene_id": 1,
    "section": "Intro / Verse 1",
    "image_type": "story | performance | climax | atmosphere",
    "location": "string (영어) — 촬영 장소",
    "action": "string (영어) — 주요 동작/사건",
    "mood": "string (영어) — 해당 장면 분위기",
    "prompt_core": "string (영어) — 이미지 프롬프트 핵심 문장 1줄"
  }
]
```

**image_type 정의:**

| 타입 | 비율 | 설명 |
|------|------|------|
| `performance` | 40~50% | 기존 보컬/악기 공연 컷 유지 |
| `story` | 30~40% | 가사 서사 장면 (신규) |
| `climax` | 10~15% | 후렴 절정 장면 |
| `atmosphere` | 10% | 분위기·실루엣 (기존 유지) |

### 3.4 전체 예시 (노래: "환승역")

```json
{
  "song_title": "환승역",
  "core_emotion": "이별 후 서로를 놓지 못하는 미련",
  "story_theme": "환승역에서 우연히 마주친 전 연인이 서로를 바라보다 헤어지는 이야기",
  "characters": ["AI Boy", "AI Girl"],
  "main_location": "neon-lit subway transfer station at night",
  "symbols": ["passing train", "platform gap", "eye contact through crowd", "flickering LED board"],
  "story_arc": {
    "intro": "텅 빈 환승역 플랫폼, 늦은 밤",
    "verse": "AI Boy가 반대편 플랫폼에서 AI Girl을 발견",
    "pre_chorus": "시선이 마주치지만 사람들 사이로 멀어짐",
    "chorus": "열차가 출발하며 둘 사이를 가로막음",
    "bridge": "AI Boy가 달려가지만 문이 닫힘",
    "final_chorus": "다음 열차를 기다리며 같은 플랫폼에 서는 두 사람",
    "outro": "열차가 떠나고 텅 빈 플랫폼에 AI Boy 혼자"
  },
  "scenes": [
    {
      "scene_id": 1,
      "section": "Intro",
      "image_type": "atmosphere",
      "location": "empty neon subway platform at night",
      "action": "wide shot of empty platform, LED signs flickering",
      "mood": "lonely anticipation",
      "prompt_core": "empty neon-lit subway platform at night, flickering LED departure board, no people, cinematic wide angle"
    },
    {
      "scene_id": 2,
      "section": "Verse 1",
      "image_type": "story",
      "location": "crowded subway transfer station",
      "action": "AI Boy spots AI Girl across the platform through the crowd",
      "mood": "sudden recognition, bittersweet",
      "prompt_core": "AI Boy chibi toy robot figure sees AI Girl chibi toy robot across crowded neon subway platform, eye contact through passengers, warm backlight glow"
    },
    {
      "scene_id": 3,
      "section": "Pre-Chorus",
      "image_type": "story",
      "location": "subway platform edge",
      "action": "AI Boy moves closer but crowd separates them",
      "mood": "reaching, longing",
      "prompt_core": "AI Boy chibi robot reaching forward through crowd toward AI Girl, soft neon blur motion, people streaming between them"
    },
    {
      "scene_id": 4,
      "section": "Chorus",
      "image_type": "climax",
      "location": "subway train doors closing",
      "action": "train doors close between AI Boy and AI Girl",
      "mood": "heartbreak, sudden separation",
      "prompt_core": "subway train doors closing between AI Boy and AI Girl chibi robots, bright platform lights, motion blur train departure, dramatic lighting contrast"
    },
    {
      "scene_id": 5,
      "section": "Bridge",
      "image_type": "story",
      "location": "subway platform",
      "action": "AI Boy runs toward the departing train but it's too late",
      "mood": "desperate, helpless",
      "prompt_core": "AI Boy chibi robot running along empty platform toward departing train taillights, motion blur, solitary figure under fluorescent lights"
    },
    {
      "scene_id": 6,
      "section": "Final Chorus",
      "image_type": "performance",
      "location": "subway-themed stage",
      "action": "both AI Boy and AI Girl on opposing sides of stage",
      "mood": "longing, unresolved",
      "prompt_core": "AI Boy and AI Girl chibi robots standing on opposite ends of neon subway-themed stage, soft spotlight, looking toward each other"
    },
    {
      "scene_id": 7,
      "section": "Outro",
      "image_type": "atmosphere",
      "location": "empty subway platform",
      "action": "single figure standing alone as last train departs",
      "mood": "acceptance, melancholy",
      "prompt_core": "lone AI Boy chibi robot standing on empty subway platform, last train disappearing into tunnel, dim overhead lights, cinematic stillness"
    }
  ],
  "_meta": {
    "generated_by": "story_analyzer.py",
    "generated_at": "2026-06-13T00:00:00",
    "model": "claude-sonnet-4-6",
    "input_file": "input/환승역.txt",
    "version": "1.0",
    "reviewed": false
  }
}
```

---

## 4. story_analyzer.py 설계

### 4.1 위치 및 역할

```
ai_img_video_aiBoygirl/
  story_analyzer.py        ← 신규 파일
```

역할: `input/*.txt` → `story_metadata.json` 생성 (Claude API 사용)

### 4.2 함수 구조

```python
# story_analyzer.py

def analyze_story(song: Song, model: str = "claude-sonnet-4-6") -> dict:
    """
    Song 객체 → story_metadata dict 반환
    
    내부 흐름:
    1. build_analysis_prompt(song) → 분석 요청 프롬프트 생성
    2. call_claude_api(prompt) → JSON 응답 수신
    3. parse_story_response(response) → dict 파싱 및 검증
    4. 반환
    """

def build_analysis_prompt(song: Song) -> str:
    """
    Claude에게 보낼 가사 분석 요청 프롬프트 구성
    
    포함 내용:
    - 곡 제목, 장르, 무드, 감정
    - 섹션별 가사 전문
    - JSON 출력 스키마 명시
    - 제약 조건 (가사 직역 금지, 상징화 지시)
    """

def parse_story_response(response_text: str) -> dict:
    """
    Claude 응답에서 JSON 추출 및 스키마 검증
    
    검증 항목:
    - 필수 키 존재 (song_title, core_emotion, story_arc, scenes)
    - scenes 최소 3개 이상
    - image_type 유효값 확인
    - prompt_core 영어 여부
    """

def save_story_metadata(metadata: dict, output_dir: Path) -> Path:
    """
    output/{곡제목}/story_metadata.json 저장
    반환: 저장된 파일 경로
    """

def load_story_metadata(song_folder: Path) -> dict | None:
    """
    기존 story_metadata.json 로드 (없으면 None)
    재생성 여부 판단에 사용
    """
```

### 4.3 Claude API 프롬프트 전략

**중간 산출물 강제 원칙:** "스토리 만들어줘"가 아니라 단계별 JSON 강제 출력

```
Step 1: 가사 요약 (1~2문장)
Step 2: 핵심 감정 추출 (단어 1개)
Step 3: 등장인물·장소·상징 추출 (JSON)
Step 4: MV 서사 로그라인 생성 (1문장)
Step 5: 섹션별 story_arc 생성 (JSON)
Step 6: scene 목록 생성 (JSON)
→ 최종 단일 JSON 출력
```

**핵심 제약 조건 (프롬프트에 명시):**

```
- 가사를 영상에서 직역하지 말 것
- 감정·상징·관계·움직임만 시각화할 것
- 심장이 빛나 → 가슴에 LED heart signal, 네온 조명
- 모든 prompt_core는 영어로 작성
- 캐릭터는 반드시 "AI Boy chibi toy robot figure" 또는 "AI Girl chibi toy robot" 표현 사용
- 폭력·혐오·사실적 인체 표현 금지
```

### 4.4 오류 처리

| 상황 | 처리 방식 |
|------|---------|
| API 호출 실패 | 재시도 1회 후 경고 출력, 건너뜀 |
| JSON 파싱 실패 | 원본 응답을 `.raw` 파일로 저장하고 경고 |
| 스키마 검증 실패 | `reviewed: false` 표시 후 저장 (수동 검수 필요) |
| scenes 0개 | 오류 발생, 해당 곡 건너뜀 |

---

## 5. main.py 통합 계획

### 5.1 통합 위치

```python
# main.py create_song_folder() 함수 내부
# 현재: 1104줄 근방

def create_song_folder(song: Song, template_dir: Path, output_dir: Path) -> Path:
    folder = output_dir / sanitize(song.title)
    folder.mkdir(parents=True, exist_ok=True)

    # [신규] story_metadata.json 생성 (story_scene 프롬프트 필요 시)
    story_meta = None
    if USE_STORY_MODE:
        story_meta = _get_or_create_story_metadata(song, folder)

    for tmpl in sorted(template_dir.glob("*.md")):
        text = read_text(tmpl)
        adapted = adapt_prompt_text(tmpl.name, text, song, story_meta)  # story_meta 추가
        write_text(folder / tmpl.name, adapted)
    
    ...
```

### 5.2 신규 템플릿 파일 추가

```
templates/
  ...기존 01~09 유지...
  10_story_scene_prompt.md    ← 신규 (story 타입 장면용)
  11_climax_scene_prompt.md   ← 신규 (climax 타입 장면용)
```

### 5.3 플레이스홀더 추가 (replacement_map 확장)

```python
# 신규 플레이스홀더
"[STORY_LOCATION]"    → story_meta["scenes"][n]["location"]
"[STORY_ACTION]"      → story_meta["scenes"][n]["action"]
"[STORY_MOOD]"        → story_meta["scenes"][n]["mood"]
"[STORY_PROMPT_CORE]" → story_meta["scenes"][n]["prompt_core"]
```

### 5.4 production_config.json 업데이트

```json
{
  "modes": {
    "mvp": {
      "clips": {
        "vocal": 2,
        "stage": 2,
        "atmosphere": 1,
        "story_scene": 3,    ← 신규: 기존 guitar/bass/drum 대체 가능
        "climax_scene": 1,   ← 신규
        "guitar": 1,
        "bass": 1,
        "drum": 1
      }
    }
  }
}
```

---

## 6. CLI 인터페이스

### 6.1 신규 명령어

```powershell
# 단일 곡 story_metadata.json 생성
python main.py analyze --title "환승역" --input input\환승역.txt

# 전체 곡 일괄 분석
python main.py analyze-all --input-dir input --output-dir output

# 스토리 모드로 프롬프트 생성 (analyze + create)
python main.py create --title "환승역" --story-mode

# 스토리 메타데이터 검수 보고
python main.py review-stories --output-dir output
```

### 6.2 기존 명령어 유지

```powershell
# 기존 공연 모드 (변경 없음)
python main.py create --title "환승역" --input input\환승역.txt
python main.py create-all --input-dir input --force
python main.py validate --folder output\환승역
```

---

## 7. 출력 구조 변화

### 현재

```
output/환승역/
  01_master_style_prompt.md
  02_style_lock_prompt.md
  03_vocal_image_prompt.md
  04_guitar_image_prompt.md
  05_bass_image_prompt.md
  06_drum_image_prompt.md
  07_stage_image_prompt.md
  08_atmosphere_image_prompt.md
  09_video_motion_prompts.md
  00_prompt_overview.md
  README.md
```

### 스토리 모드 추가 후

```
output/환승역/
  ...기존 01~09 유지...
  story_metadata.json          ← 신규
  10_story_scene_prompt.md     ← 신규 (scene별 이미지 프롬프트)
  11_climax_scene_prompt.md    ← 신규 (클라이맥스 장면)
  00_prompt_overview.md        ← 스토리 요약 포함으로 확장
  README.md                    ← 스토리 섹션 추가
```

---

## 8. 구현 순서 (Phase)

### Phase 1 — story_analyzer.py 독립 구현 (우선순위: 최고)

- [ ] `story_analyzer.py` 파일 생성
- [ ] `build_analysis_prompt()` 구현
- [ ] Claude API 호출 (`anthropic` 패키지 사용)
- [ ] `parse_story_response()` + 스키마 검증
- [ ] `save_story_metadata()` 구현
- [ ] CLI: `python story_analyzer.py "환승역" input\환승역.txt` 단독 실행 지원
- [ ] 테스트: 5곡으로 결과 검수

### Phase 2 — 스토리 프롬프트 템플릿 작성

- [ ] `templates/10_story_scene_prompt.md` 작성
- [ ] `templates/11_climax_scene_prompt.md` 작성
- [ ] `adapt_prompt_text()` 에 story_meta 처리 추가

### Phase 3 — main.py 통합

- [ ] `create_song_folder()` 에 story_meta 흐름 추가
- [ ] `replacement_map()` 에 `[STORY_*]` 플레이스홀더 추가
- [ ] `production_config.json` 에 story_scene 항목 추가
- [ ] `command_create()` 에 `--story-mode` 플래그 추가
- [ ] `validate_song_folder()` 에 story_metadata.json 검증 추가

### Phase 4 — 테스트 및 검증

- [ ] `tests/test_story_analyzer.py` 작성
- [ ] 10곡 이상 end-to-end 테스트
- [ ] 기존 326개 테스트 회귀 없음 확인

---

## 9. 의존성

```
anthropic          ← Claude API (기존 .env의 ANTHROPIC_API_KEY 사용)
python-dotenv      ← .env 로드 (기존 사용 중)
pytest             ← 테스트 (기존 사용 중)
```

신규 패키지 없음. 기존 환경 그대로 사용.

---

## 10. 설계 원칙

1. **기존 공연 모드는 건드리지 않는다** — `--story-mode` 플래그로 완전 분리
2. **반자동 우선** — story_metadata.json 생성 후 수동 검수(`reviewed: true`) 완료 후 프롬프트 생성
3. **가사 직역 금지** — 감정·상징·움직임만 시각화
4. **캐릭터 일관성 유지** — "AI Boy/AI Girl chibi toy robot figure" 표현 강제
5. **기존 테스트 회귀 없음** — 신규 기능은 별도 파일로 분리

---

## 11. 미결 사항 (검토 필요)

| 항목 | 옵션 A | 옵션 B | 결정 필요 |
|------|--------|--------|----------|
| API 모델 | claude-sonnet-4-6 (현재) | claude-opus-4-8 (고품질) | 비용 vs 품질 |
| 스토리:공연 비율 | 30:70 | 50:50 | 장르별 다르게 |
| story_metadata 위치 | output/{곡}/story_metadata.json | input/{곡}_story.json | 재생성 편의성 |
| 수동 검수 방식 | `reviewed` 플래그 수동 변경 | web_app.py에 검수 UI 추가 | 편의성 |

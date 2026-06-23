# AI 뮤직비디오 제작 가이드
## output 프롬프트 → GPT 이미지 → Flow/Kling 영상 → CapCut 편집

---

## 전체 흐름 요약

```
1단계: GPT 이미지 생성 (01~08번 프롬프트)
        ↓  이미지 6장 완성
2단계: Kling/Flow에서 각 이미지를 3번씩 영상화 (Variant A/B/C)
        ↓  클립 26~32개 완성
3단계: CapCut에서 편집 맵 따라 조립
        ↓
    완성 MV
```

---

## 1단계: GPT에서 이미지 생성

### 준비물
- `output/{곡제목}/` 폴더 안의 `01~08번 .md` 파일
- `reference/` 폴더 안의 PNG 이미지 9개 (장르별 기준 캐릭터 이미지)

---

### 순서 1 — 마스터 스타일 이미지 (01번)

**목적:** 전체 MV의 시각 기준을 세우는 첫 번째 이미지. 여기서 나온 이미지가 이후 모든 장면의 기준이 됩니다.

1. ChatGPT 열기 → 이미지 생성 모드 (GPT-4o 또는 GPT-image)
2. **첨부:** `reference/` 폴더의 장르에 맞는 PNG(또는 `base.png`)를 드래그해서 올리기
3. **프롬프트:** `01_master_style_prompt.md` 파일 열기 → 코드 블록(```)안의 텍스트 전체 복사 → 붙여넣기
4. 이미지 생성 → 마음에 들면 저장 (`01_master.png`)

> **팁:** 이 이미지가 MV 전체 분위기를 결정합니다. 색감, 조명, 밴드 구도가 마음에 들 때까지 재생성하세요.

---

### 순서 2 — 스타일 고정 확인 (02번)

**목적:** 이후 개별 이미지가 마스터에서 벗어나지 않도록 기준을 잡는 참조 프롬프트입니다.  
실제로 이미지를 새로 만들기보다, 이후 이미지 생성 시 **이 프롬프트를 함께 참조용으로 첨부**합니다.

- `02_style_lock_prompt.md`는 이미지 생성보다는 **체크리스트 역할**
- 이후 각 이미지 생성 시 "이 내용을 유지하는지" 확인

---

### 순서 3 — 전체 무대 이미지 (07번) ← **중요, 먼저 생성**

**목적:** 밴드 4명이 모두 보이는 와이드 샷. 이 이미지를 가장 먼저 만들어야 이후 개별 멤버 이미지와 일관성이 맞습니다.

1. ChatGPT에서 새 대화 시작
2. **첨부:** `reference/` 장르 PNG + 앞서 만든 `01_master.png`
3. **프롬프트:** `07_stage_image_prompt.md` 코드 블록 전체 복사 → 붙여넣기
4. 저장 (`07_stage.png`)

> **팁:** `01_master.png`를 함께 첨부하면 마스터와 같은 색감·조명이 유지됩니다.

---

### 순서 4 — 개별 멤버 이미지 (03~06, 08번)

**각 이미지 공통 방법:**

1. ChatGPT 새 대화 또는 이어서
2. **첨부:** `reference/` 장르 PNG + `01_master.png` + `07_stage.png`
3. 해당 번호 프롬프트 코드 블록 복사 → 붙여넣기
4. 저장

| 번호 | 파일명 | 내용 | 저장명 제안 |
|------|--------|------|------------|
| 03 | `03_vocal_image_prompt.md` | 보컬 클로즈업 | `03_vocal.png` |
| 04 | `04_guitar_image_prompt.md` | 기타리스트 | `04_guitar.png` |
| 05 | `05_bass_image_prompt.md` | 베이시스트 | `05_bass.png` |
| 06 | `06_drum_image_prompt.md` | 드러머 | `06_drum.png` |
| 08 | `08_crowd_image_prompt.md` | 관중 | `08_crowd.png` |

**생성 순서 권장:** 07(무대) → 03(보컬) → 04(기타) → 05(베이스) → 06(드럼) → 08(관중)

---

### 이미지 생성 완료 체크리스트

```
□ 01_master.png  — 전체 분위기 기준
□ 03_vocal.png   — 보컬 클로즈업
□ 04_guitar.png  — 기타리스트
□ 05_bass.png    — 베이시스트
□ 06_drum.png    — 드러머
□ 07_stage.png   — 전체 무대 와이드
□ 08_crowd.png   — 관중

확인사항:
□ 모든 이미지에서 AI Boy/AI Girl 캐릭터 디자인(의상, 색상, 헬멧)이 동일한가?
□ 마스터 이미지(01번)와 색감이 일치하는가?
□ 치비 토이 로봇 피규어가 실사 사람으로 바뀌지 않았는가?
```

---

## 2단계: Kling AI에서 영상 클립 생성

### 핵심 원리: 이미지 1개 → 클립 여러 개

```
03_vocal.png (이미지 1장)
    ↓ Variant A 프롬프트 적용 → 클립 1 (5~8초)
    ↓ Variant B 프롬프트 적용 → 클립 2 (5~8초)
    ↓ Variant C 프롬프트 적용 → 클립 3 (5~8초)
    → 총 3개 보컬 클립 완성
```

같은 이미지를 세 번 업로드해서 서로 다른 카메라 움직임·동작 프롬프트를 적용합니다.

---

### Kling AI 사용 방법

#### 기본 프롬프트로 첫 번째 클립 만들기

1. [Kling AI](https://klingai.com) 접속 → **Video** → **Image to Video**
2. 이미지 업로드: `03_vocal.png`
3. `09_video_motion_prompts.md` 파일 열기
4. **"보컬 영상"** 섹션의 코드 블록 텍스트 복사:
   ```
   Animate the uploaded image while preserving the band/world identity...
   Song title: {곡제목}
   Stage energy: ...
   slow cinematic handheld push-in,
   ...
   ```
5. Kling 프롬프트 창에 붙여넣기
6. Duration: **5-8 seconds** / Mode: **Kling 2.0 Pro** 또는 **Turbo**
7. 생성 → 저장: `vocal_base.mp4`

---

#### Variant A/B/C로 추가 클립 만들기

같은 `03_vocal.png`를 **다시 업로드**하고, 이번에는 Variant 텍스트를 사용합니다.

`09_video_motion_prompts.md`에서 **"Motion Variants Per Image"** → **"Vocal Variants"** 섹션을 찾습니다:

```
Variant A - emotional push-in:
slow cinematic handheld push-in toward the AI Boy/AI Girl figure,
screen-face display showing the emotional beat,
chibi hand gesture between phrases,
soft smoke crossing the foreground,
5 to 8 seconds

Variant B - low-angle chorus peak:
dynamic low-angle camera push toward the AI Boy/AI Girl figure,
screen-face display brightening on the chorus peak,
[CHARACTER_COLOR] backlight pulsing harder,
crowd silhouettes flashing behind,
5 to 8 seconds

Variant C - side tracking shot:
side-angle tracking movement around the AI Boy/AI Girl figure,
chibi hand holding prop, other hand gesture near chest,
smoke and particles drifting past the lens,
5 to 8 seconds
```

**적용 방법:**

| 생성 회차 | 업로드 이미지 | 사용할 프롬프트 | 저장명 |
|---------|-------------|--------------|-------|
| 1번 | `03_vocal.png` | 보컬 영상 기본 프롬프트 | `vocal_base.mp4` |
| 2번 | `03_vocal.png` (재업로드) | Vocal Variant A 전체 텍스트 | `vocal_A.mp4` |
| 3번 | `03_vocal.png` (재업로드) | Vocal Variant B 전체 텍스트 | `vocal_B.mp4` |
| 4번 | `03_vocal.png` (재업로드) | Vocal Variant C 전체 텍스트 | `vocal_C.mp4` |

> **중요:** Variant 프롬프트는 독립적으로 사용합니다. 기본 프롬프트와 합치지 마세요.
> Kling은 "Do not ask Kling to create all variants inside one generation"이라고 명시되어 있습니다.

---

### 악기별 생성 계획 (3분 MV 기준 — 26클립)

| 이미지 | 기본 프롬프트 | Variant | 총 클립 수 |
|-------|------------|---------|----------|
| 보컬 (`03_vocal.png`) | 보컬 영상 기본 | A, B, C → 4개 중 5개 선택 | **5클립** |
| 기타 (`04_guitar.png`) | 기타 영상 기본 | A, B, C → 4개 중 5개 선택 | **5클립** |
| 베이스 (`05_bass.png`) | 베이스 영상 기본 | A, B | **3클립** |
| 드럼 (`06_drum.png`) | 드럼 영상 기본 | A, B | **3클립** |
| 무대 (`07_stage.png`) | 전체 무대 영상 기본 | A, B, C → 5개 | **5클립** |
| 관중 (`08_crowd.png`) | 군중 영상 기본 | A, B, C → 5개 | **5클립** |
| **합계** | | | **26클립** |

4분 MV 기준으로는 32클립 (각 악기별 1~3개 추가).

---

### Kling 프롬프트 입력 팁

Kling은 **40~60단어**가 최적입니다. Variant 텍스트가 그 이상이면 앞부분 핵심만 사용:

```
✅ 좋은 예 (45단어):
Wide shot: AI Boy/AI Girl chibi toy figures perform a warm R&B song on stage,
vocalist and guitarist moving in sync,
warm amber light glowing above the stage,
crowd phone lights swaying below,
slow cinematic wide pan, bittersweet concert atmosphere.
The movement settles into stillness.

❌ 너무 긴 예:
Animate the uploaded image while preserving... (100단어 이상)
```

`09_video_motion_prompts.md`의 **"## Kling AI"** 섹션은 이미 40~60단어로 최적화된 전용 프롬프트입니다. 다른 플랫폼 섹션을 쓰지 말고 반드시 Kling 섹션만 사용하세요.

---

## 2단계(대안): Google Flow에서 영상 클립 생성

### Flow 사용 방법

1. [Google Flow](https://labs.google.com/flow) 접속
2. **New Project** → 곡 제목으로 프로젝트 생성
3. **+ Add clip** → **Image to Video**
4. 이미지 업로드
5. `09_video_motion_prompts.md`에서 **"## Google Flow (Veo Workflow)"** 섹션의 프롬프트 사용
6. **Style:** Cinematic / Anime 선택
7. Duration: 5~8초
8. 생성

### Flow vs Kling 차이점

| 항목 | Kling | Flow (Veo) |
|------|-------|-----------|
| 캐릭터 일관성 | 높음 | 중간 |
| 카메라 움직임 | 정확 | 자연스러움 |
| 애니메이션 스타일 | 3D 사실적 | 더 영화적 |
| 사용 난이도 | 쉬움 | 중간 |
| 권장 사용 | 개별 악기 클로즈업 | 전체 무대·군중 와이드샷 |

**추천 분담:**
- Kling: 보컬, 기타, 베이스, 드럼 (캐릭터 클로즈업 중요)
- Flow: 전체 무대, 군중 (와이드샷, 분위기 중요)

---

## 3단계: CapCut에서 MV 편집

### CapCut 편집 맵 활용

`09_video_motion_prompts.md` 맨 아래 **"CapCut Editing Map"** 섹션을 엽니다:

```
Intro: stage A, crowd B, vocal A
Verse 1: vocal A, bass A, guitar B, drum A
Pre-Chorus: stage B, vocal C
Chorus 1: stage B, vocal B, guitar C, drum B, crowd C
Verse 2: vocal C, bass B, guitar A, crowd A
Bridge or Solo: guitar A, drum C, stage A
Final Chorus: stage C, vocal B, guitar C, drum B, crowd C
Outro: stage C or crowd B
```

**이 맵을 읽는 방법:**

- `stage A` = `07_stage.png`로 만든 **Variant A** 클립 = `stage_A.mp4`
- `vocal B` = `03_vocal.png`로 만든 **Variant B** 클립 = `vocal_B.mp4`
- `guitar C` = `04_guitar.png`로 만든 **Variant C** 클립 = `guitar_C.mp4`

---

### 편집 단계별 작업

#### Step 1: 음악 파일 배치
1. CapCut 새 프로젝트
2. 곡 MP3 파일을 타임라인 오디오 트랙에 올리기
3. 곡의 섹션 위치 파악 (LRC 파일이 있다면 타임스탬프 참조)

#### Step 2: 클립 순서대로 배치
편집 맵 순서에 따라 각 클립을 타임라인에 배치:

```
[Intro 구간]
  └─ stage_A.mp4 (6초) → crowd_B.mp4 (4초) → vocal_A.mp4 (5초)

[Verse 1 구간]
  └─ vocal_A.mp4 (8초) → bass_A.mp4 (6초) → guitar_B.mp4 (5초) → drum_A.mp4 (5초)

[Pre-Chorus 구간]
  └─ stage_B.mp4 (6초) → vocal_C.mp4 (5초)

[Chorus 1 구간]
  └─ stage_B.mp4 → vocal_B.mp4 → guitar_C.mp4 → drum_B.mp4 → crowd_C.mp4
  (각 3~5초, 빠른 컷)
```

#### Step 3: 컷 속도 조절

| 구간 | 컷 속도 | 이유 |
|------|--------|------|
| Intro | 클립당 6~10초 | 분위기 설정 |
| Verse | 클립당 5~8초 | 서사 진행 |
| Pre-Chorus | 클립당 4~6초 | 긴장감 |
| **Chorus** | **클립당 1~3초** | **최고 에너지** |
| Bridge | 클립당 4~6초 | 감정 전환 |
| Final Chorus | 클립당 1~3초 | 클라이맥스 |
| Outro | 클립당 6~10초 | 여운 |

#### Step 4: 트랜지션

- Chorus 진입: **빠른 컷** (트랜지션 없음)
- 섹션 간: **디졸브 0.3~0.5초**
- Outro: **페이드 아웃**

---

## 클립 파일 정리 추천

생성된 클립을 다음과 같이 정리하면 편집이 편합니다:

```
output/{곡제목}/
├── images/
│   ├── 01_master.png
│   ├── 03_vocal.png
│   ├── 04_guitar.png
│   ├── 05_bass.png
│   ├── 06_drum.png
│   ├── 07_stage.png
│   └── 08_crowd.png
└── clips/
    ├── vocal_base.mp4
    ├── vocal_A.mp4
    ├── vocal_B.mp4
    ├── vocal_C.mp4
    ├── guitar_base.mp4
    ├── guitar_A.mp4
    ├── guitar_B.mp4
    ├── guitar_C.mp4
    ├── bass_base.mp4
    ├── bass_A.mp4
    ├── bass_B.mp4
    ├── drum_base.mp4
    ├── drum_A.mp4
    ├── drum_B.mp4
    ├── stage_base.mp4
    ├── stage_A.mp4
    ├── stage_B.mp4
    ├── stage_C.mp4
    ├── crowd_base.mp4
    ├── crowd_A.mp4
    ├── crowd_B.mp4
    └── crowd_C.mp4
```

---

## 전체 제작 시간 추정

| 단계 | 소요 시간 |
|------|--------|
| GPT 이미지 생성 (7장) | 30~60분 |
| Kling/Flow 클립 생성 (26개) | 2~4시간 |
| CapCut 편집 | 1~2시간 |
| **총** | **4~7시간** |

---

## 자주 묻는 질문

**Q: Variant를 꼭 다 만들어야 하나요?**  
A: 아닙니다. 최소 3분 MV는 15클립으로도 가능합니다. 보컬 3개, 기타 3개, 베이스 2개, 드럼 2개, 무대 3개, 관중 2개로 시작하세요.

**Q: 클립 길이가 너무 길거나 짧으면?**  
A: CapCut에서 클립을 트리밍하거나 속도 조절하면 됩니다. 같은 클립을 두 번 반복해서 쓰는 것도 자연스럽습니다 (특히 후렴).

**Q: 이미지마다 밴드가 조금씩 다르게 나와요.**  
A: `reference/` 폴더의 이미지를 항상 함께 첨부하고, `01_master.png`도 같이 올리세요. ChatGPT는 대화가 길어질수록 앞 참조를 잊기 때문에 새 대화에서 매번 다시 첨부하는 것이 중요합니다.

**Q: Flow와 Kling 중 뭘 써야 하나요?**  
A: 처음엔 Kling을 추천합니다. 이미지-to-비디오 품질이 안정적이고 캐릭터 일관성이 더 좋습니다. Flow는 와이드샷과 분위기 클립에 사용하세요.

**Q: Variant A/B/C 중 어느 걸 어느 섹션에 써야 할지 모르겠어요.**  
A: `09_video_motion_prompts.md` 맨 아래 **CapCut Editing Map**을 그대로 따르면 됩니다. `vocal A` = 버스용 차분한 푸시인, `vocal B` = 코러스용 로우앵글, `vocal C` = 브리지용 사이드샷으로 설계되어 있습니다.

---

## 빠른 시작 — 처음 MV 만들 때

가장 빠르게 결과물을 보려면:

```
1. GPT에서 03_vocal + 07_stage 이미지만 먼저 생성 (20분)
2. Kling에서 vocal 기본 + stage 기본 클립 생성 (30분)
3. CapCut에서 Chorus 구간만 편집 (20분)
→ 첫 코러스 클립 완성, 전체 방향 확인 가능
```

전체 MV는 이후 나머지 악기 이미지와 클립을 추가하며 완성합니다.

---

## 4단계: 곡별 README.md — 섹션별 편집 가이드 활용

각 곡 폴더(`output/{곡제목}/README.md`)에는 **가사 기준 편집 순서**가 자동 생성되어 있습니다.

### README.md 구조

```
## 3. 가사 기준 편집 순서

### Intro
  가사: 오늘따라 왜 이렇게...
  추천 컷: stage_intro_01, crowd_outro_01
  편집:
    카메라: 와이드 샷으로 시작 → close-up push-in 으로 전환
    조명: warm magenta city glow
    에너지: intimate youth R&B live performance

### Verse 1
  가사: 엘리베이터 거울 앞...
  추천 컷: vocal_verse_01, guitar_verse_01
  편집:
    카메라: 보컬 클로즈업 위주, 악기 컷 간간이 삽입
    ...
```

### CapCut 편집 맵과 README의 차이

| 항목 | CapCut 편집 맵 (09번 프롬프트) | README.md 편집 가이드 |
|------|----------------------------|--------------------|
| 내용 | Variant 코드로 간결 (`vocal_A`, `stage_B`) | 실제 가사 + 구체적 카메라/조명 설명 |
| 용도 | 클립 파일명 조합 참조 | 편집 방향 이해 |
| 사용 시점 | CapCut 타임라인 배치 시 | 어떤 느낌으로 만들지 판단 시 |

### 실제 활용 방법

1. CapCut에서 편집 전 **README.md를 먼저 읽기**
2. 각 섹션의 "추천 컷"에서 어느 악기가 중심인지 파악
3. "편집" 설명에서 카메라 느낌 확인 → 해당 Variant 선택
4. `09번 프롬프트의 CapCut 편집 맵`을 보면서 실제 클립 배치

**예시: 들리잖아 Intro 섹션**

README가 말하는 것:
```
추천 컷: stage_intro_01, crowd_outro_01
카메라: 와이드 샷으로 시작 → close-up push-in 으로 전환
```

→ `stage_A.mp4` (Variant A = 와이드 오프닝) → `crowd_B.mp4` (Variant B = 폰 불빛 드리프트)

**예시: 들리잖아 Chorus 섹션**

README가 말하는 것:
```
추천 컷: stage_chorus_01, vocal_chorus_01, crowd_chorus_01
카메라: 넓은 무대 컷 → 보컬 클로즈업 → 관중 리액션 순
```

→ `stage_B.mp4` → `vocal_B.mp4` (Variant B = 로우앵글 코러스 피크) → `crowd_C.mp4` (Variant C = 코러스 반응)

---

## 5단계: 영상 플랫폼 선택 가이드

`09_video_motion_prompts.md`에는 여러 플랫폼 섹션이 있습니다. 어떤 플랫폼을 쓸지 선택 기준:

### 플랫폼별 특성 비교

| 플랫폼 | 캐릭터 일관성 | 카메라 제어 | 속도 | 권장 사용처 |
|--------|------------|-----------|------|-----------|
| **Kling 2.0 Pro** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 중간 | **메인 악기 클로즈업** |
| **Google Flow** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 중간 | **와이드샷, 분위기** |
| **Pika 2.2** | ⭐⭐⭐⭐ | ⭐⭐⭐ | 빠름 | 빠른 테스트용 |
| **Hailuo (MiniMax)** | ⭐⭐⭐ | ⭐⭐⭐ | 빠름 | 보조 클립 |
| **Sora** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 느림 | 시네마틱 장면 |
| **PixVerse** | ⭐⭐⭐ | ⭐⭐⭐ | 빠름 | 빠른 대용량 생성 |
| **Veo (Google)** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 중간 | 자연스러운 움직임 |
| **Wan 2.2** | ⭐⭐⭐ | ⭐⭐⭐⭐ | 중간 | 1080p 고화질 필요 시 |

### 권장 조합

**빠르게 MV 완성하고 싶을 때:**
- 보컬·기타·베이스·드럼 → **Kling**
- 무대·관중 → **Flow 또는 Kling**

**최고 품질이 목표일 때:**
- 보컬 클로즈업 → **Kling**
- 무대 와이드샷 → **Sora 또는 Flow**
- 드럼 임팩트 → **Kling**
- 관중 분위기 → **Flow**

**비용 최소화:**
- 1차 생성: **Hailuo 또는 Pika** (테스트)
- 채택된 클립만 **Kling**으로 고품질 재생성

### 플랫폼별 프롬프트 사용법

`09_video_motion_prompts.md`에서 해당 플랫폼 섹션을 찾아 사용하세요:

```
## Kling AI
[Kling 전용 40~60단어 최적화 프롬프트]

## Google Flow (Veo Workflow)
[Flow 전용 프롬프트]

## Pika 2.2
[Pika 전용 + -camera -motion 플래그 포함]

## Wan 2.2
[Wan 전용 + Negative prompt 포함]
```

각 플랫폼 섹션 하단의 `>` 블록은 **해당 플랫폼 사용 팁**입니다. 읽고 참조하세요.

---

## 6단계: YouTube 업로드 설정

### CapCut 내보내기 설정

```
해상도:     1920 × 1080 (Full HD) 또는 3840 × 2160 (4K)
프레임레이트: 24fps (영화적 느낌) 또는 30fps (안정적)
비트레이트:  최고 품질 선택
코덱:       H.264 (H.265는 일부 기기 호환 문제)
파일형식:   MP4
```

### YouTube 업로드 최적화

**썸네일:** `01_master.png` 또는 `07_stage.png`를 기반으로 제작 (이미 16:9 비율)

**제목 예시:**
```
들리잖아 🎵 AI 뮤직비디오 | Animation MV [AI Music Video]
```

**태그 예시:**
```
AI뮤직비디오, AI Music Video, Korean Music, K-pop, AI Animation,
Kling AI, Suno, AI캐릭터, Chibi Robot, AI Generated
```

**설명에 포함할 내용:**
- 사용한 AI 도구 목록 (GPT-image, Kling, CapCut 등)
- 원곡 정보
- `#AIMusic #KoreanAI #AIAnimation` 해시태그

---

## 트러블슈팅

### 문제 1: 이미지마다 밴드 디자인이 다르게 나온다

**원인:** ChatGPT 대화가 길어지면 앞 내용을 잊어버립니다.

**해결:**
- 각 이미지를 **새 대화**에서 생성
- 매번 `reference/` 장르 PNG + `01_master.png` **함께 첨부**
- 02번 Style Lock 프롬프트의 "Keep the same..." 부분을 대화 맨 앞에 붙여넣기

```
[새 대화 시작 시 이렇게 입력]
Keep the same AI Boy/AI Girl chibi toy robot figure.
Keep the same screen-face display, round robot helmet, chibi toy body.
Keep the same genre outfit and color palette.
[이미지 첨부 후 실제 프롬프트 입력]
```

---

### 문제 2: Kling에서 캐릭터가 사람으로 바뀐다

**원인:** AI Boy/AI Girl 치비 토이 캐릭터가 실사 인물로 해석됩니다.

**해결:**
- 프롬프트 맨 앞에 `Preserve the character design: AI Boy/AI Girl chibi toy robot figure` 문구 확인
- Kling 설정에서 **"강도(Motion)" 낮추기** → 이미지 변형 감소
- Image-to-Video 모드인지 확인 (Text-to-Video가 아닌 I2V)
- 기준 이미지(`reference/` 폴더 PNG)를 함께 업로드

---

### 문제 3: Kling 클립이 너무 많이 움직이거나 변형됨

**원인:** 프롬프트가 너무 길거나 모션 강도가 높습니다.

**해결:**
- **Motion 강도:** 0.3~0.5 (기본값보다 낮게)
- 프롬프트 40~60단어로 줄이기
- `Do not redesign the band` 문구를 프롬프트 끝에 추가

---

### 문제 4: 이미지 색상이 R&B/발라드인데 록/메탈처럼 보인다

**원인 (해결됨):** 과거 버전의 이미지 프롬프트는 록 기본값을 썼습니다.  
현재 버전에서는 장르별로 자동 교체됩니다.

**현재 상태 확인:**
```python
python main.py create --title "곡제목" --input input/곡파일.txt --force
```
재생성 후 `04_guitar_image_prompt.md`에서 `dark synthwave metal`이 없으면 정상입니다.

---

### 문제 5: Flow에서 생성하면 밴드가 너무 사실적(실사)으로 나온다

**해결:**
- Style 설정에서 **Anime** 또는 **Animation** 선택
- 프롬프트에 `3D cinematic anime render`, `non-photorealistic` 명시
- Flow보다 **Kling** 사용 권장 (애니메이션 스타일 더 유지)

---

### 문제 6: 클립 클립이 너무 부드럽지 않아 편집 시 어색하다

**원인:** 클립 시작/끝이 갑자기 멈추거나 시작됩니다.

**해결:**
- CapCut에서 클립 시작/끝에 **0.3초 페이드** 추가
- 또는 연속된 두 클립을 **J컷/L컷**으로 오디오 먼저/나중에 연결
- Kling 프롬프트에 `smooth motivated transition at the end` 문구 있는지 확인 (이미 포함됨)

---

## 전체 플로우 한눈에 보기

```
[새 곡 추가]
  ↓
python main.py create --input input/{곡}.txt
  ↓
output/{곡제목}/ 폴더 생성
├── README.md            ← 섹션별 편집 가이드 (먼저 읽기)
├── 00_prompt_overview.md ← 전체 프롬프트 한글 설명
├── 01_master_style_prompt.md
├── 02_style_lock_prompt.md
├── 03_vocal_image_prompt.md
├── 04_guitar_image_prompt.md
├── 05_bass_image_prompt.md
├── 06_drum_image_prompt.md
├── 07_stage_image_prompt.md
├── 08_crowd_image_prompt.md
└── 09_video_motion_prompts.md ← Variant A/B/C + CapCut 맵 포함
  ↓
[GPT 이미지 생성] — reference/ 첨부 필수
07_stage → 01_master → 03_vocal → 04_guitar → 05_bass → 06_drum → 08_crowd
  ↓
[Kling / Flow 영상 생성]
각 이미지 × (기본 + Variant A + B + C) = 클립 26~32개
  ↓
[CapCut 편집]
CapCut Editing Map 참조 + README.md 섹션별 가이드 참조
  ↓
[YouTube 업로드]
1080p or 4K / 24fps / H.264
```

---

## 자주 쓰는 명령어

```powershell
# 새 곡 프롬프트 생성
python main.py create --title "곡제목" --input input/곡파일.txt

# 전체 input 폴더 일괄 생성
python main.py create-all --input-dir input --force

# 특정 곡 재생성 (기존 덮어쓰기)
python main.py create --title "곡제목" --input input/곡파일.txt --force

# 생성된 프롬프트 품질 확인
python main.py summarize-all --input-dir input --output-dir output

# 이전 곡 정보가 남아있는지 검증
python main.py validate --folder output/곡제목 --previous-term "이전곡제목"
```

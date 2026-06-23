# AI Anime MV 제작 가이드
## 이미지 생성 → Kling 영상 → CapCut 편집

---

## 전체 흐름 요약

```
1단계: 캐릭터 시트 생성 (00_character_sheet.md)
        ↓  캐릭터 확정
2단계: 씬 이미지 생성 (01_image_prompts.md, 씬당 6개 플랫폼)
        ↓  이미지 7장 완성
3단계: Kling AI에서 씬당 Variant A/B/C 클립 생성 (02_video_prompts.md)
        ↓  클립 14~28개 완성
4단계: CapCut에서 편집 맵 따라 조립 (02_video_prompts.md 하단 CapCut Editing Map)
        ↓
    완성 MV
```

---

## 1단계: 캐릭터 시트 생성

### 준비물
- `output/{곡제목}/00_character_sheet.md`

### 순서

1. Nijijourney (--niji 7) 또는 GPT Image 열기
2. `00_character_sheet.md`에서 해당 플랫폼 프롬프트 복사 → 붙여넣기
3. 캐릭터 8-뷰 시트 생성 → 저장 (`character_sheet.png`)

> **중요:** 이 시트가 MV 전체 캐릭터의 기준이 됩니다. 이후 모든 씬 이미지와 Kling 생성 시 반드시 첨부.

---

## 2단계: 씬 이미지 생성

### 준비물
- `output/{곡제목}/01_image_prompts.md`
- `character_sheet.png` (1단계 결과물)

### 씬별 생성 방법

1. GPT Image 또는 Nijijourney 열기
2. `character_sheet.png` 첨부 (필수)
3. `01_image_prompts.md` 에서 해당 씬의 프롬프트 복사 → 붙여넣기
4. 저장: `scene_01.png`, `scene_02.png` ... `scene_NN.png`

| 씬 | 저장명 권장 |
|----|-----------|
| Scene 01 — Intro | `scene_01.png` |
| Scene 02 — Verse 1 | `scene_02.png` |
| Scene NN — ... | `scene_NN.png` |

### 이미지 생성 완료 체크리스트

```
□ 모든 씬 이미지에서 캐릭터 외형이 동일한가?
□ character_sheet.png를 모든 씬 생성 시 첨부했는가?
□ 곡 고유 색상(Color Main)이 유지되는가?
□ 다른 곡의 캐릭터 특징이 섞이지 않았는가?
```

---

## 3단계: Kling AI에서 영상 클립 생성

### 핵심 원리: 이미지 1장 → 클립 여러 개

```
scene_04.png (이미지 1장)
    ↓ Base 프롬프트 적용 → scene_04_base.mp4 (5-8초)
    ↓ Variant A 프롬프트 적용 → scene_04_A.mp4 (5-8초)
    ↓ Variant B 프롬프트 적용 → scene_04_B.mp4 (5-8초)
    ↓ Variant C 프롬프트 적용 → scene_04_C.mp4 (5-8초)
    → 4개 클립 완성 (동일 캐릭터, 다른 카메라·강도)
```

### Kling AI 사용 방법

1. [Kling AI](https://klingai.com) 접속 → **Video** → **Image to Video**
2. 씬 이미지 업로드: `scene_NN.png`
3. `02_video_prompts.md` 열기 → 해당 씬의 **Base** 코드블록 텍스트 복사 → 붙여넣기
4. Duration: **5-8 seconds** / Mode: **Kling 2.0 Pro** 또는 **Standard**
5. 저장: `scene_NN_base.mp4`

### Variant A/B/C 추가 클립

같은 씬 이미지를 **다시 업로드**하고 Variant 텍스트를 적용합니다.

| Variant | 특성 | 사용 섹션 |
|---------|------|---------|
| **A — Quiet Presence** | 거의 정지, 주변 환경 모션만 | Intro, Verse, Outro |
| **B — Emotional Arc** | 느린 push-in, 캐릭터 자세 변화 | Pre-Chorus, Bridge |
| **C — Peak Moment** | 다이나믹 카메라, 조명 피크 | Chorus, Final Chorus |

### 클립 생성 계획 (3분 MV 기준)

```
최소 (14클립): 씬당 2클립 × 7씬
권장 (21클립): 씬당 3클립 × 7씬
최대 (28클립): 씬당 4클립 × 7씬

코러스 섹션: C + B 클립 반복 사용 (자연스러움, 권장)
```

---

## 4단계: CapCut에서 MV 편집

### CapCut Editing Map 활용

`output/{곡제목}/02_video_prompts.md` 맨 아래 **CapCut Editing Map** 섹션을 엽니다.

```
예시 (10년 후에도):
Intro          (8-10초): scene_01_A
Verse 1        (5-8초): scene_02_base → scene_02_A
Pre-Chorus     (4-6초): scene_03_B
Chorus         (1-3초): scene_04_B → scene_04_C → scene_04_B → scene_04_C
Bridge         (5-7초): scene_05_A → scene_05_B
Chorus         (1-3초): scene_06_B → scene_06_C → scene_06_B → scene_06_C
Outro          (8-10초): scene_07_A
```

### 편집 단계별 작업

#### Step 1: 음악 파일 배치
1. CapCut 새 프로젝트 (16:9, 1920×1080)
2. `input/{곡제목}.mp3`를 오디오 트랙에 올리기

#### Step 2: 클립 배치
CapCut Editing Map 순서대로 클립을 타임라인에 배치합니다.

#### Step 3: 컷 속도 조절

| 구간 | 클립 지속 시간 | 이유 |
|------|-------------|------|
| Intro | 8-10초 | 분위기 설정 |
| Verse | 5-8초 | 서사 진행 |
| Pre-Chorus | 4-6초 | 긴장감 |
| **Chorus** | **1-3초** | **에너지 피크** |
| Bridge | 5-7초 | 감정 전환 |
| **Final Chorus** | **1-3초** | **클라이맥스** |
| Outro | 8-10초 | 여운 |

#### Step 4: 트랜지션

```
Chorus 진입  : 빠른 하드컷 (트랜지션 없음)
섹션 간       : 디졸브 0.3-0.5초
Outro 종료    : 페이드 아웃
```

---

## 클립 파일 정리 추천

```
output/{곡제목}/
├── character_sheet.png      ← 1단계 생성
├── scene_01.png             ← 2단계 생성
├── scene_02.png
├── ...
├── scene_NN.png
├── clips/
│   ├── scene_01_A.mp4       ← 3단계 생성
│   ├── scene_02_base.mp4
│   ├── scene_02_A.mp4
│   ├── scene_03_B.mp4
│   ├── scene_04_B.mp4
│   ├── scene_04_C.mp4
│   └── ...
└── 00_character_sheet.md    ← 프롬프트 파일
    01_image_prompts.md
    02_video_prompts.md
    03_production_guide.md
    README.md
```

---

## 전체 제작 시간 추정

| 단계 | 소요 시간 |
|------|---------|
| 캐릭터 시트 생성 | 20-40분 |
| 씬 이미지 생성 (7장) | 30-60분 |
| Kling 클립 생성 (21개) | 1.5-3시간 |
| CapCut 편집 | 30-60분 |
| **총** | **3-5시간** |

---

## 자주 묻는 질문

**Q: Variant를 꼭 다 만들어야 하나요?**
A: 아닙니다. 최소한 Chorus씬만 B+C 두 가지를 만들면 됩니다. Intro/Outro는 A 하나로 충분합니다.

**Q: 코러스가 두 번 반복되는데 씬이 다른가요?**
A: 네, scene_04 (Chorus 1)와 scene_06 (Chorus 2)는 다른 이미지입니다. 하지만 CapCut에서 scene_04_C를 scene_06 구간에 재사용하는 것도 자연스럽습니다.

**Q: Kling에서 캐릭터 외형이 바뀌면?**
A: `00_character_sheet.md` 이미지를 보조 참조로 업로드하세요. Kling v2.0 Pro의 Character Consistency 기능을 사용하면 됩니다.

**Q: 클립이 너무 많이 움직이거나 변형되면?**
A: Kling Motion 강도를 0.3-0.5로 낮추고 프롬프트를 40-60단어로 줄이세요.

---

## 빠른 시작 — 처음 MV 만들 때

```
1. 00_character_sheet.md → Nijijourney에서 캐릭터 시트 생성 (20분)
2. 01_image_prompts.md → Chorus씬(scene_04) 이미지 먼저 생성 (10분)
3. Kling에서 scene_04_B + scene_04_C 클립 생성 (20분)
4. CapCut에서 Chorus 구간만 편집 (10분)
→ 첫 코러스 클립 완성, 전체 방향 확인 가능
```

전체 MV는 이후 나머지 씬 이미지와 클립을 순서대로 추가하며 완성합니다.

---

## 자주 쓰는 명령어

```powershell
# 새 곡 프롬프트 생성
python main.py create --song "곡이름"

# 전체 input 폴더 일괄 생성
python main.py create-all --force

# 출력 검증
python main.py validate
```

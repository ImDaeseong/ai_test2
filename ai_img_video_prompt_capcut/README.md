# ai_img_video_prompt_capcut

Suno 음원 + LRC 파일을 분석해 CapCut MV 편집용 타임라인(`timeline.json`)과 편집 가이드(`shot_list.md`)를 자동 생성하는 CLI 도구.

---

## 개요

```
ai_img_video_aiBoygirl 출력물
  (09_video_motion_prompts.md + 이미지)
           ↓
    Kling 클립 생성
           ↓
  input/{곡명}/clips/ 배치
           ↓
  main.py build
           ↓
  timeline.json   ← CapCut 배치 좌표 (ms 단위)
  shot_list.md    ← 편집자용 가이드
           ↓
  main.py export-draft
           ↓
  CapCut PC 드래프트 자동 생성
```

- LRC 섹션 마커(Intro / Verse / Chorus …)를 파싱해 섹션별 시작·종료 시각을 계산
- 곡 폴더 내 `*_video_motion_prompts.md`의 `## CapCut Editing Map`을 우선 사용 → 없으면 `production_config.json` 폴백
- `clips/` 폴더의 mp4 파일을 자동 매핑, 없으면 placeholder로 표시
- `"or"` 구문(예: `stage A or atmosphere A`) 지원 — 첫 번째 클립 없으면 두 번째 자동 사용
- SRT 파일이 있으면 CapCut 드래프트에 자막 트랙 자동 삽입 (한글 + 영어 분리 트랙)

---

## 설치

```powershell
pip install click mutagen
```

> `mutagen` 없이도 동작하지만 WAV 이외 포맷의 오디오 길이 측정과 mp4 클립 길이 비교 기능이 비활성화됩니다.

---

## 입력 폴더 구조

```
input/
└─ {곡명}/
   ├─ {곡명}.wav                    # 음원 (mp3·m4a·flac도 가능)
   ├─ *.lrc                         # Suno 가사 다운로더 파일 (섹션 타임스탬프 포함)
   ├─ *.srt                         # 한글 자막 (선택)
   ├─ *_en.srt                      # 영어 자막 (선택)
   ├─ *_video_motion_prompts.md     # ai_img_video_aiBoygirl 생성 파일 (곡별 CapCut 맵)
   └─ clips/
      ├─ vocal_A.mp4
      ├─ vocal_B.mp4
      ├─ vocal_C.mp4
      ├─ guitar_A.mp4
      ├─ guitar_B.mp4
      ├─ bass.mp4
      ├─ drum.mp4
      ├─ stage_A.mp4
      ├─ stage_B.mp4
      ├─ stage_C.mp4
      ├─ atmosphere_A.mp4
      └─ atmosphere_B.mp4
```

- **clips/** 폴더가 없거나 비어 있어도 빌드는 완료됩니다 (placeholder 모드).
- 파일명 대소문자는 무시됩니다(`vocal_A.mp4` = `Vocal_a.mp4`).

---

## 사용법

### 1. inspect — 입력 상태 점검

```powershell
python main.py inspect --song UPGRADE
```

- 음원·LRC·SRT·clips/ 존재 여부 확인
- 섹션 타임라인 미리보기
- 사용 중인 CapCut 맵 소스 표시
- 필수 클립 누락 경고 (`❌ 필수` / `⚠️ fallback 있음`)
- 클립 실제 길이 vs 섹션 길이 비교 (클립이 짧으면 CapCut 루프/슬로모 필요 경고)

```
=== UPGRADE 점검 ===
음원   : ✅ UPGRADE.wav (4:02)
LRC    : ✅ ...lrc
SRT    : ✅ ...srt
Clips  : ✅ 12개
           atmosphere_a → atmosphere_A.mp4
           bass → bass.mp4
           ...

섹션 9개:
  Intro                0:00 ~ 0:20
  Verse 1              0:20 ~ 0:58
  Pre-Chorus           0:58 ~ 1:14
  Chorus               1:14 ~ 1:52
  Verse 2              1:52 ~ 2:29
  Bridge               2:29 ~ 2:50
  Guitar Solo          2:50 ~ 2:58
  Chorus               2:58 ~ 3:35
  Outro                3:35 ~ 4:02
CapCut 맵: 09_video_motion_prompts.md

✅ 필요 클립 모두 준비됨

⚠️  짧은 클립 (CapCut 루프/슬로모 필요):
   stage_A.mp4  5.2s < 20.8s
   ...
```

---

### 2. plan — 섹션 매핑 미리보기

```powershell
python main.py plan --song UPGRADE
```

파일을 생성하지 않고 섹션 → shot_type 매핑과 클립 가용 여부를 확인합니다.

```
=== UPGRADE 섹션 매핑 === (09_video_motion_prompts.md)
  Intro                0:00 ~ 0:20  →  [Intro]  ✅stage_A, ✅atmosphere_A, ✅vocal_A
  Verse 1              0:20 ~ 0:58  →  [Verse 1]  ✅vocal_A, ✅bass, ✅guitar_A, ✅drum
  Pre-Chorus           0:58 ~ 1:14  →  [Pre-Chorus]  ✅stage_B, ✅vocal_B
  Chorus               1:14 ~ 1:52  →  [Chorus 1]  ✅stage_B, ✅vocal_B, ✅guitar_A, ✅drum, ✅atmosphere_A
  Verse 2              1:52 ~ 2:29  →  [Verse 2]  ✅vocal_B, ✅bass, ✅guitar_A, ✅atmosphere_A
  Bridge               2:29 ~ 2:50  →  [Bridge/Solo]  ✅guitar_A, ✅drum, ✅stage_A
  Guitar Solo          2:50 ~ 2:58  →  [Bridge/Solo]  ✅guitar_A, ✅drum, ✅stage_A
  Chorus               2:58 ~ 3:35  →  [Final Chorus]  ✅stage_B, ✅vocal_B, ✅guitar_A, ✅drum, ✅atmosphere_A
  Outro                3:35 ~ 4:02  →  [Outro]  ✅stage_A

✅ 준비 완료: 30/30 슬롯 (100%)
```

헤더 `(09_video_motion_prompts.md)`는 곡별 맵이 적용됐음을 의미합니다. `production_config.json`을 사용하면 `(production_config.json)`으로 표시됩니다.

- `✅shot` : 클립 준비됨
- `✅shot→fallback` : primary 없음, fallback 클립으로 대체
- `⚠️shot` : 클립 없음 (Kling 생성 필요)

---

### 3. build — 파일 생성

```powershell
python main.py build --song UPGRADE
python main.py build --song UPGRADE --keep 3   # 히스토리 3개만 유지
```

`output/{곡명}/{YYYYMMDD_HHMMSS}/` 에 두 파일을 생성하고 `output/{곡명}/latest/` 를 항상 최신 빌드로 갱신합니다.

```
[UPGRADE] 빌드 시작...
   CapCut 맵: 09_video_motion_prompts.md
✅ 완료 → output\UPGRADE\20260609_204207
   슬롯 30개 (할당 30 / 플레이스홀더 0)
   ⚠️  stage_A.mp4  클립 5.2s < 섹션 20.8s  (15.6s 부족 — CapCut 루프/슬로모 필요)
   latest/ 갱신 완료  (mode: mvp)
```

| 생성 파일 | 내용 |
|-----------|------|
| `timeline.json` | 섹션·클립 슬롯 전체 (ms 단위), 빌드 메타데이터 포함 |
| `shot_list.md` | CapCut 편집자용 테이블 + 작업 순서 가이드 |

**`--keep N`** : 오래된 run_id 폴더를 자동 삭제해 N개만 유지합니다 (0 = 전체 유지, 기본값).

---

### 4. build-all — 전체 배치 처리

```powershell
python main.py build-all
python main.py build-all --keep 3
```

`input/` 폴더 내 모든 곡을 순서대로 빌드하고 집계 통계를 출력합니다.

---

## 출력 파일 구조

### timeline.json (schema_version 1.2)

```json
{
  "schema_version": "1.2",
  "build_info": {
    "generated_at": "2026-06-09T20:42:07",
    "mode": "mvp"
  },
  "song_title": "UPGRADE",
  "total_duration_ms": 242952,
  "sections": [
    {
      "name": "Intro",
      "capcut_key": "Intro",
      "start_ms": 0,
      "end_ms": 20787,
      "duration_ms": 20787
    }
  ],
  "clips": [
    {
      "slot_id": "intro_stage_A",
      "section": "Intro",
      "capcut_key": "Intro",
      "shot_type": "stage_A",
      "start_ms": 0,
      "end_ms": 20787,
      "duration_ms": 20787,
      "clip_file": "stage_A.mp4",
      "source": "assigned",
      "review_required": false
    }
  ]
}
```

| 필드 | 설명 |
|------|------|
| `build_info.mode` | 빌드 시 사용된 모드 (`mvp` / `full`) |
| `source` | `assigned` = 클립 매핑됨, `placeholder` = 클립 없음 |
| `review_required` | `true`면 Kling 클립 생성 후 교체 필요 |
| `fallback_used` | fallback 클립을 사용한 경우에만 존재, 사용된 shot명 기록 |

---

## 곡별 CapCut 맵 (`*_video_motion_prompts.md`)

`ai_img_video_aiBoygirl`이 생성하는 `09_video_motion_prompts.md` 파일 내 `## CapCut Editing Map` 섹션을 자동으로 읽어 곡별 맵으로 사용합니다.

```markdown
## CapCut Editing Map

```text
Intro       : stage A, atmosphere A, vocal A
Verse 1     : vocal A, bass, guitar A, drum
Pre-Chorus  : stage B, vocal B
Chorus 1    : stage B, vocal B, guitar A, drum, atmosphere A
Verse 2     : vocal B, bass, guitar A, atmosphere A
Bridge/Solo : guitar A, drum, stage A
Final Chorus: stage B, vocal B, guitar A, drum, atmosphere A
Outro       : stage A or atmosphere A
```
```

- 파일이 있으면 곡별 맵 **우선 적용**
- 파일 없으면 `production_config.json` **폴백**
- 곡마다 다른 섹션 구성(Bridge 유무, Verse 개수 등)을 자동 반영

---

## production_config.json 설정 (전역 폴백)

곡 폴더에 `*_video_motion_prompts.md`가 없는 경우에만 이 파일을 사용합니다.

```json
{
  "mode": "mvp",
  "modes": {
    "mvp": {
      "capcut_map": {
        "sections": [
          "Intro       : stage A, atmosphere A, vocal A",
          "Chorus 1    : stage B, vocal B, guitar A, drum, atmosphere A",
          "Outro       : stage A or atmosphere A"
        ]
      }
    }
  }
}
```

- **모드 전환**: `"mode"` 값을 `"mvp"` ↔ `"full"` 로 바꾸고 `build` 재실행
- **`or` 구문**: `stage A or atmosphere A` — stage_A 없으면 atmosphere_A 자동 사용
- **shot_type 규칙 변경**: `production_config.json`만 수정, `main.py`는 건드리지 않음

---

### 5. export-draft — CapCut PC 드래프트 자동 생성

```powershell
python main.py export-draft --song UPGRADE
```

`build` 후 실행하면 CapCut 드래프트 폴더에 직접 프로젝트를 생성합니다.

```
[UPGRADE] CapCut 드래프트 생성...
   타임라인: 1.2 / 30슬롯 (30 할당)
   음원: UPGRADE.wav  (243.0s)
   자막(KR): ...srt → 45개 항목
   자막(EN): *_en.srt 없음 — 영어 자막 트랙 생략

✅ 드래프트 생성 완료
   위치  : C:\Users\...\com.lveditor.draft\{draft_id}\
   이름  : UPGRADE_MV
   영상  : 30개 세그먼트
   자막  : 45개 세그먼트

   CapCut 실행 → 프로젝트 목록에서 'UPGRADE_MV' 확인
```

**생성 파일:**
- `draft_content.json` — 트랙·세그먼트·material 전체 (CapCut 8.x JSON 포맷)
- `draft_meta_info.json` — 프로젝트 이름·ID·파일 목록

**자막 트랙:**

| 트랙 | 소스 | 텍스트 크기 | 위치 |
|------|------|------------|------|
| 한글 | `*.srt` (Part2 실제 가사만 추출) | 20pt | 화면 하단 (y = -0.75) |
| 영어 | `*_en.srt` | 16pt | 한글 아래 (y = -0.88) |

Suno SRT는 Part1(압축 섹션 마커)과 Part2(실제 가사)로 구성됩니다. `[End]` 마커 이후 Part2만 추출하고 `[대괄호]` 형식 줄은 제외합니다.

**타임라인 전략:** 섹션 내 클립들을 균등 분할해 메인 비디오 트랙에 순서대로 배치.
클립 실제 길이 < 세그먼트 길이면 `is_loop: true` 자동 설정 (CapCut이 루프 재생).

> CapCut이 실행 중이면 종료 후 실행하세요. 재시작 시 프로젝트 목록에 나타납니다.

---

## 권장 워크플로우

```
1. ai_img_video_aiBoygirl에서 곡 처리
   → 09_video_motion_prompts.md 생성됨 (CapCut 맵 포함)

2. Suno에서 음원 + LRC + SRT 다운로드

3. input/{곡명}/ 구성
   ├─ {곡명}.wav
   ├─ *.lrc
   ├─ *.srt                      (선택)
   ├─ *_en.srt                   (선택)
   ├─ 09_video_motion_prompts.md (ai_img_video_aiBoygirl 출력)
   └─ clips/  ← Kling 생성 클립 배치

4. python main.py inspect --song {곡명}   # 입력 상태 + 누락 클립 확인
5. python main.py plan    --song {곡명}   # 섹션 매핑 검토 (곡별 맵 적용 확인)
6. python main.py build   --song {곡명}   # timeline.json 생성
7. python main.py export-draft --song {곡명}   # CapCut 프로젝트 자동 생성
8. CapCut 재시작 → '{곡명}_MV' 프로젝트 열기 → 편집 시작
```

---

## 의존성

| 패키지 | 용도 | 필수 여부 |
|--------|------|-----------|
| `click` | CLI 인터페이스 | 필수 |
| `mutagen` | WAV 외 오디오 길이 측정, mp4 클립 길이 비교 | 권장 |

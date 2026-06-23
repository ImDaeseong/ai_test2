# 설계 문서 — ai_img_video_prompt_capcut

> Suno 음원 + LRC → CapCut MV 타임라인 자동 생성 CLI
> 외부 AI API 없음. 의존성: click, mutagen (선택).

---

## 1. 목적과 범위

`ai_img_video_prompt`로 생성한 Kling 영상 클립을 CapCut에서 편집할 때, 섹션별 클립 배치 타임라인을 자동 계산한다. LRC 파일의 섹션 타임스탬프를 파싱해 CapCut에서 바로 열 수 있는 드래프트 JSON까지 생성한다.

**이 프로젝트의 위치**:
```
ai_img_video_prompt (프롬프트 생성)
        ↓
   Kling AI (영상 생성) → clips/*.mp4
        ↓
ai_img_video_prompt_capcut (타임라인 자동 계산)
        ↓
    CapCut (편집)
```

---

## 2. 아키텍처

```
main.py (click CLI)
├── inspect      입력 상태 점검 (음원·LRC·clips 누락 검사, 클립 길이 비교)
├── plan         섹션 매핑 미리보기 (클립 가용 여부 ✅/⚠️)
├── build        timeline.json + shot_list.md 생성
├── build-all             전체 곡 배치 처리 + 통계
├── sync                  ai_lyric_video/input/{곡}의 오디오·자막 파일 동기화
├── export-lyric-draft    완성된 가사 영상 → CapCut 드래프트 생성 (오디오·자막 분리)
├── export-image-lyric-draft  이미지 + 오디오 + LRC → CapCut 드래프트 직접 생성
└── export-draft          CapCut 드래프트 JSON 생성 (바로 열기 가능)

capcut_draft.py
└── CapCut 8.x JSON 포맷 생성 (draft_content.json + draft_meta_info.json)

실행.bat
└── input/ 곡 자동 감지 → build → export-draft 원클릭 실행
```

---

## 3. 데이터 흐름

```
input/{곡명}/
├── {곡명}.wav          → mutagen으로 전체 길이 측정
├── *.lrc               → 섹션 타임스탬프 파싱
└── clips/
    ├── vocal_A.mp4     → mutagen으로 클립 길이 측정
    └── ...

LRC 파싱
  └→ [(timestamp_ms, section_label), ...]
  └→ 섹션별 (start_ms, end_ms) 계산

production_config.json
  └→ capcut_map: {section_type: [shot_type, ...]}
     mode: "mvp" (12클립) / "full" (24클립)

섹션 × shot_type 매핑
  └→ clips/ 폴더에서 파일 탐색 (대소문자 무시)
     "or" 구문 처리: "stage A or atmosphere A" → 첫 번째 없으면 두 번째
  └→ SlotList: [{section, shot_type, clip_path, start_ms, end_ms, duration_ms}, ...]

SlotList
  └→ timeline.json   (schema_version 1.2)
  └→ shot_list.md    (편집자용 가이드 테이블)
  └→ output/{곡명}/{YYYYMMDD_HHMMSS}/

export-draft
  └→ capcut_draft.py → draft_content.json + draft_meta_info.json
     CapCut 설치 경로 아래 드래프트 폴더에 복사 → CapCut 재시작 시 자동 인식
```

---

## 4. 핵심 설계 결정

### 4-1. LRC 타임스탬프 파싱

Suno LRC 파일은 `[mm:ss.xx]` 형식으로 섹션 마커를 포함한다. 파서는 이 마커를 ms 단위로 변환하고, 다음 마커의 시작이 현재 마커의 종료가 된다.

```
[00:00.00] Intro
[00:15.30] Verse 1
[01:02.10] Chorus
```
→ Intro: 0~15300ms, Verse 1: 15300~62100ms, ...

마지막 섹션의 종료는 음원 전체 길이로 계산 (mutagen 필요).

### 4-2. "or" Fallback 클립

`production_config.json`의 capcut_map에 `"stage A or atmosphere A"` 형식으로 fallback을 지정할 수 있다. 첫 번째 클립이 없을 경우 두 번째를 자동 사용.

```json
{
  "chorus": ["vocal_A", "stage A or atmosphere A", "guitar_A"]
}
```

### 4-3. 클립 루프 처리

클립 실제 길이가 섹션 길이보다 짧으면 `"is_loop": true`로 마킹. CapCut에서 루프 설정 필요 경고도 함께 출력.

### 4-4. MVP / Full 모드

`production_config.json`에서 `mode`로 선택:
- `mvp`: 12클립 (핵심 역할만)
- `full`: 24클립 (모든 Variant 포함)

### 4-5. 출력 히스토리 관리

`--keep N` 플래그로 최근 N개 빌드만 유지. `output/{곡명}/latest/`는 항상 최신 빌드로 자동 심링크.

### 4-6. CapCut 드래프트 포맷 (8.x)

```json
draft_content.json: {
  "tracks": [{
    "segments": [{
      "material_id": "...",
      "source_timerange": {"start": 0, "duration": 5000000},  // μs 단위
      "target_timerange": {"start": 0, "duration": 5000000}
    }]
  }]
}
```

**주의**: CapCut 내부 시간 단위는 **μs(마이크로초)** — ms가 아님.

---

## 5. 입력 파일 구조

```
input/
└─ {곡명}/
   ├─ {곡명}.wav          # 음원 (mp3·m4a·flac 가능, mutagen 필요)
   ├─ *.lrc               # 섹션 타임스탬프 포함 가사 파일
   ├─ *.srt               # 자막 (선택, 미사용 시 무시)
   └─ clips/
      ├─ vocal_A.mp4
      ├─ vocal_B.mp4
      ├─ guitar_A.mp4
      ├─ bass.mp4
      ├─ drum.mp4
      ├─ stage_A.mp4
      ├─ stage_B.mp4
      ├─ atmosphere_A.mp4  # 2026-06-08 crowd → atmosphere 전환
      └─ ...
```

---

## 6. production_config.json 구조

```json
{
  "mode": "mvp",
  "modes": {
    "mvp": {
      "capcut_map": {
        "sections": [
          "Intro        : stage_A, atmosphere_A, vocal_A",
          "Verse 1      : vocal_A, guitar_A, bass, drum",
          "Pre-Chorus   : stage_B, vocal_B",
          "Chorus 1     : stage_B, vocal_B, guitar_A, drum, atmosphere_A",
          "Bridge/Solo  : guitar_A, drum, stage_A",
          "Final Chorus : stage_B, vocal_B, guitar_B, drum, atmosphere_A",
          "Outro        : stage_A or atmosphere_A"
        ]
      }
    }
  }
}
```

**주의**: 섹션 키는 `match_sections()`이 생성하는 키와 정확히 일치해야 한다:  
`Intro` / `Verse 1` / `Verse 2` / `Pre-Chorus` / `Chorus 1` / `Final Chorus` / `Bridge/Solo` / `Outro`

**2026-06-08 변경**: `crowd_A` → `atmosphere_A`, `crowd_B` → `atmosphere_B`로 전환 완료.

---

## 7. 알려진 버그 패턴

| 증상 | 원인 | 해결 |
|---|---|---|
| slot_id 충돌 | 동일 섹션명(Chorus)이 여러 번 등장 | suffix 자동 부여 (Chorus_1, Chorus_2) — 이미 수정됨 |
| CapCut에서 드래프트 안 보임 | CapCut 미재시작 | CapCut 완전 종료 후 재시작 |
| 클립 길이 측정 실패 | mutagen 미설치 | `pip install mutagen` |
| 마지막 섹션 길이 이상 | 음원 길이 측정 실패 | mutagen 설치 또는 wav 파일 사용 |
| "or" 구문 모두 없음 | clips/ 폴더 비어있음 | placeholder 모드로 동작 (빌드는 완료됨) |

---

## 8. 확장 시 주의사항

- **새 역할 추가(예: keyboard)**: `production_config.json`의 capcut_map에 추가, clips/ 폴더에 해당 파일 배치.
- **CapCut 버전 대응**: 드래프트 포맷이 버전마다 다를 수 있음. `capcut_draft.py`의 `new_version` 값 업데이트 필요.
- **시간 단위 주의**: `timeline.json`은 ms, CapCut 드래프트는 μs. 변환 계산 누락 시 타이밍 전부 오차.
- **crowd 표현 제거**: 2026-06-08 이후 crowd 관련 클립명/매핑은 atmosphere로 교체됨.

---

## 9. 테스트 전략

```
python -m pytest tests_unit.py -q   →  65 passed (2026-06-23 기준)
```

| 테스트 그룹 | 대상 | 수량 |
|---|---|---|
| `SECTION_RE` | 유효/무효 섹션명 정규식 (intro~post_chorus, 무효 2종) | 9 |
| `load_config` | 모드·샷 파싱, `or` fallback, 콜론 없는 라인 스킵 | 3 |
| `normalize_timestamps` | end_ms 계산, 빈 리스트, 오디오 없음, 스케일링 3종 | 6 |
| `match_sections` | intro, chorus 순위, bridge/solo, pre/post-chorus | 6 |
| `build_slots` | 할당, placeholder, slot_id 중복 방지, fallback, duration_ms | 5 |
| `normalize_label` | explosive/build/final chorus 변환, 무변환 4종 | 7 |
| `parse_lrc` | explosive chorus 감지, pre-chorus 끝 타이밍 | 2 |
| `parse_srt` | Part1 스킵, 대괄호 필터, 타임스탬프 변환 | 3 |
| `parse_capcut_map_from_md` | 기본 파싱, 섹션 없는 파일 | 2 |
| μs 변환 | 0, 1초, 실값 변환 | 3 |
| `draft_content` JSON | 필수 키, 해상도, 길이, materials 키 | 4 |
| `draft_meta` JSON | 필수 키, 이름 포맷, ID 일관성, 길이 | 4 |
| 자막 트랙 | SRT 없음·단일·복수 트랙 구성 | 3 |
| `write_draft` | 폴더 생성, draft_id 폴더명, 경로 기록, JSON 유효성 | 4 |
| 클립 길이 미지정 | 기본값 사용 (섹션 길이로 대체 금지) | 1 |
| 트랜지션 | 섹션 경계 삽입, 첫 섹션 제외, 두 번째 섹션 refs | 3 |

**검증 명령어**
```powershell
python -m py_compile main.py capcut_draft.py   # 문법 검사
python -m pytest tests_unit.py -q              # 단위 테스트
python main.py inspect --song {곡명}            # 실제 입력 상태 확인
```

---

*Last Updated: 2026-06-23*

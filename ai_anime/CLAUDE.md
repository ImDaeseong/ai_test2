# CLAUDE.md — ai_anime

> 애니메이션 MV 이미지·영상 프롬프트 자동 생성 프로젝트
> 외부 AI API 없이 순수 Python 템플릿 치환 엔진으로 동작합니다.
> 곡 정보 txt → 5종 프롬프트 자동 출력 (캐릭터 시트·이미지·영상·제작가이드·README)

---

## 절대 규칙

- **외부 API 호출 금지**: 이 프로젝트는 외부 AI API를 사용하지 않는다.
- **하드코딩 금지**: 장르·색상·스타일 값을 코드에 직접 쓰지 않는다. 모든 값은 `anime_profiles.json` 또는 `templates/`에서 참조한다.
- **output/ 직접 편집 금지**: `output/` 폴더의 파일은 `main.py`로만 생성한다.
- **정책 안전화 우회 금지**: `SAFETY_RISK_MAP` 필터를 제거하거나 우회하지 않는다.

---

## 파일 역할

| 파일 | 역할 | 수정 시 주의사항 |
|---|---|---|
| `main.py` | 파이프라인 진입점 | `create`, `create-all`, `validate` 명령 처리 |
| `anime_profiles.json` | 7개 장르 프로파일 | 환경·카메라샷·모션 값의 유일한 출처 |
| `templates/00_character_sheet.md` | 캐릭터 시트 템플릿 | `[PLACEHOLDER]` 형식 — 직접 값 입력 금지 |
| `templates/01_image_prompts.md` | 씬 이미지 프롬프트 템플릿 | `[SCENE_IMAGE_BLOCKS]` 플레이스홀더 |
| `templates/02_video_prompts.md` | 씬 영상 프롬프트 템플릿 | `[SCENE_VIDEO_BLOCKS]` 플레이스홀더 |
| `templates/03_production_guide.md` | 제작 가이드 템플릿 | 메타데이터 + 워크플로우 |
| `input/` | 곡 정보 txt 파일 | 수정 금지 (입력 데이터) |
| `output/` | 곡별 생성 결과 | 직접 편집 금지 |
| `tests_unit.py` | pytest 단위 테스트 | 수정 후 전체 통과 확인 필수 |

---

## 입력 파일 형식 (`input/*.txt`)

```
Song Title: 곡 제목
Genre: 장르 설명
BPM: 숫자 또는 unknown
Mood: 분위기
Emotion: 감정
Tempo: 템포
Stage Energy: 무대 에너지
Lighting Style: 조명 스타일
Song Motif: 곡의 핵심 시각적 모티프
Color Palette Rule: 색상 팔레트 규칙
Color Main: 메인 색상
Color Base: 기본 배경색
Character: 주인공 설명
Character Silhouette: 실루엣
Character Hair: 헤어
Character Outfit: 의상
Character Prop: 소품
Genre Profile: anime_profiles.json 키값 (예: telephone-signal-pop)
```

---

## 검증 명령어

```bash
# 단위 테스트
python -m pytest tests_unit.py -v

# 곡 프롬프트 생성
python main.py create-all

# 출력 검증
python main.py validate
```

---

## 완료 기준

- pytest 전체 통과
- `python main.py create-all` 실행 후 각 곡 폴더에 5개 파일 생성 확인
- `python main.py validate` 실행 후 모든 폴더 PASS

---

## 자주 발생하는 문제

| 문제 | 원인 | 해결 |
|---|---|---|
| `[SCENE_IMAGE_BLOCKS]` 미치환 | 템플릿에 오타 | 템플릿 파일 확인 |
| `KeyError` in profile | `Genre Profile` 키가 JSON에 없음 | `anime_profiles.json`에 해당 키 추가 |
| 미치환 플레이스홀더 | txt 파일에 해당 필드 누락 | input txt에 필드 추가 |

---

*Last Updated: 2026-06-07*

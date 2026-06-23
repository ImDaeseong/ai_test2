# Testing Reference — ai_img_video_prompt_capcut

## 실행

```powershell
python -m pytest tests_unit.py -v
```

## 테스트 항목 (65개)

| 분류 | 테스트 수 | 커버 범위 |
|------|-----------|-----------|
| `SECTION_RE` | 9 | 유효/무효 섹션명 패턴 (intro~post_chorus, 무효 2종) |
| `load_config` | 3 | 모드 로드, `or` 구문, 콜론 없는 줄 무시 |
| `normalize_timestamps` | 6 | end_ms 설정, 빈 섹션, audio_ms 없음, 스케일링 3종 |
| `match_sections` | 6 | Intro, Chorus 순위, Bridge/Solo, Pre/Post-Chorus |
| `build_slots` | 5 | 할당, placeholder, slot_id 중복, fallback, duration_ms |
| `normalize_label` | 7 | explosive/build/final chorus 변환, 무변환 4종 |
| `parse_lrc` | 2 | explosive chorus 감지, pre-chorus 끝 타이밍 |
| `parse_srt` | 3 | Part1 스킵, 대괄호 필터, 타임스탬프 변환 |
| `parse_capcut_map_from_md` | 2 | 기본 파싱, `## CapCut Editing Map` 없는 파일 |
| μs 변환 | 3 | 0, 1초, 실값 변환 |
| `draft_content` JSON | 4 | 필수 키, 해상도, 길이, materials 키 |
| `draft_meta` JSON | 4 | 필수 키, 이름 포맷, ID 일관성, 길이 |
| 자막 트랙 | 3 | SRT 없음·단일·복수 트랙 구성 |
| `write_draft` | 4 | 폴더 생성, draft_id 폴더명, 경로 기록, JSON 유효성 |
| 클립 길이 미지정 | 1 | 기본값 사용 (섹션 길이로 대체 금지) |
| 트랜지션 | 3 | 섹션 경계 삽입, 첫 섹션 제외, 두 번째 섹션 refs |

## 주의사항

- 모든 테스트는 네트워크·외부 API 없이 실행됩니다.
- `mutagen` 없이도 테스트 통과 (오디오 길이 비교 테스트는 skip).
- `capcut_draft.py` 문법 검사: `python -m py_compile capcut_draft.py`

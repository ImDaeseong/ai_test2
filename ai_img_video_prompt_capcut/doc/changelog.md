# Changelog — ai_img_video_prompt_capcut

## 2026-06-09

| 항목 | 내용 |
|------|------|
| CapCut 드래프트 자동 생성 | `export-draft` 명령 안정화 (CapCut 8.x JSON) |
| 한글 자막 트랙 | SRT Part2 추출 → CapCut text 트랙 자동 삽입 |
| 영어 자막 트랙 | `*_en.srt` 별도 트랙 (size 16, y=-0.88) |
| 곡별 CapCut 맵 | `*_video_motion_prompts.md` 우선 사용, `production_config.json` 폴백 |
| Verse 2 누락 해결 | 곡별 맵 사용으로 `production_config.json` Verse 2 누락 문제 자동 회피 |

## 2026-06-08

| 항목 | 내용 |
|------|------|
| crowd → atmosphere 전환 | `crowd_A/B` → `atmosphere_A/B`, 코드·문서 전체 반영 |

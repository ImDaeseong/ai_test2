# Handoff

## Goal

`ai_img_video_prompt`에 실존 공연 자료를 일반화한 이미지·영상 연출 프로필을 적용한다.

## Implementation

- 공연 프로필 8종
- 공식 출처 7건
- 이미지별 무대·조명·카메라·퍼포먼스 변형
- 영상용 카메라 이동·피사체 동작·관객 동작·조명 동작·전환 제안
- 결정론적 선택과 실존 아티스트 비노출
- `validate_output.py`를 읽기 전용 전수 검증으로 변경

## Verification

- `pytest -q`: 334 passed
- `python -u validate_output.py`: 214곡 전체 PASS
- 대표곡 `UPGRADE`, `감기`, `구독취소` 재생성 및 개별 검증 통과
- 대표 프롬프트 실존 밴드명 검색 0건
- 214곡이 8개 공연 프로필에 분산됨

## Human Review

공개 전 대표 3곡 이상의 실제 생성 이미지와 영상 클립을 비교한다.

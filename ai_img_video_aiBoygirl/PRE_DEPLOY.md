# Pre-Deploy

## Automated

- [x] pytest 전체 통과: 334 passed
- [x] `validate_output.py` 전체 통과: 214곡 PASS
- [x] Python 구문 검사 통과
- [x] 대표 3곡 생성 및 폴더 검증 통과
- [x] 실존 밴드명 프롬프트 검색 0건

## Human Hold

- [ ] 대표 이미지·영상의 공연 문법 다양성 확인
- [ ] 기존 스켈레톤 밴드 정체성 확인
- [ ] 실존 공연의 얼굴·로고·의상·고유 무대 복제 없음 확인

## Rollback

이전 `main.py`를 복원하고 `performance_profiles.json`을 제거한 뒤 기존 출력물을 다시 생성한다.

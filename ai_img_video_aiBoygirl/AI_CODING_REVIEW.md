# AI Coding Review

## Review

- 기존 장르 프로필과 템플릿을 교체하지 않고 공연 연출 계층을 추가했다.
- 외부 API와 신규 패키지를 추가하지 않았다.
- 특정 곡 제목 분기가 없다.
- 데이터 추가는 JSON으로 가능하다.
- SHA-256 기반 선택이라 Python hash seed와 무관하게 재현 가능하다.

## Security And Rights

- 비밀값, 개인정보, 회사 데이터 없음
- 실존 밴드명은 provenance 데이터에만 존재
- 생성 프롬프트에서 실존 아티스트 모방을 명시적으로 금지
- reference 기반 기존 밴드 정체성 유지

## Remaining Human Review

텍스트 검증만으로 시각적 유사성을 완전히 판단할 수 없으므로 생성된 이미지와 영상 클립을 사람이 검수해야 한다.


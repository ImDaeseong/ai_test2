# Project Start: Performance Reference Profiles

## Purpose

실제 밴드 공연의 일반적인 무대·조명·카메라·동작·전환 문법을 사용해 이미지와 영상 프롬프트의 반복성을 낮춘다.

## Safety Boundary

- 공식 공개 자료만 조사 출처로 기록한다.
- 실존 밴드명은 출처 문서와 설정 메타데이터에만 둔다.
- 생성 프롬프트에는 실존 얼굴, 로고, 정확한 의상, 고유 소품, 시그니처 무대 복제를 넣지 않는다.
- 기존 오리지널 스켈레톤 밴드와 reference 이미지 정체성을 유지한다.
- 특정 곡 제목 분기와 하드코딩을 금지한다.

## Architecture

- `genre_profiles.json`: 기존 장르별 음악 분위기와 역할
- `performance_profiles.json`: 공연 제작 프로필 8종과 공식 출처
- `select_performance_profile()`: 장르, BPM, Mood, Emotion, Stage Energy 기반 선택
- `performance_direction_block()`: 이미지용 구도와 영상용 이동·전환 지시 생성
- SHA-256 기반 선택으로 같은 곡은 재실행해도 같은 결과를 얻는다.

## Acceptance Criteria

1. 기존 9개 출력 파일 계약과 캐릭터 락을 유지한다.
2. 이미지 파일마다 카메라·조명 변형을 적용한다.
3. 영상 파일에는 카메라 이동, 피사체 동작, 관객 동작, 조명 동작, CapCut 전환 제안을 포함한다.
4. 대표 장르가 서로 다른 공연 프로필로 분류된다.
5. 생성 프롬프트에 조사 대상 실존 밴드명이 포함되지 않는다.
6. 기존 전체 테스트와 출력 검증이 통과한다.

## Human Hold

실제 생성 이미지·영상 3곡 이상을 비교해 다양성, 캐릭터 일관성, 실존 공연 복제 위험을 사람이 확인하기 전에는 공개 배포 완료로 판단하지 않는다.


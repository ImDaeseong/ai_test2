# 4. 운영과 변경 대응

## 출시 전 HOLD

- `HOLD-META-APP`: 앱 설정, 권한 승인, Live 상태 증거
- `HOLD-LIVE-OAUTH`: 실제 사용자 동의와 토큰 교환, 비밀 마스킹 증거
- `HOLD-LIVE-PUBLISH`: 사용할 유형별 실제 생성·상태·게시·조회 증거
- `HOLD-WEBHOOK-CONTRACT`: 최신 필드, 서명, 재전송 동작 증거
- `HOLD-POLICY`: 개인정보, 삭제, 보존, 저작권에 대한 사람 검토
- `HOLD-CHANGE`: changelog 또는 응답 스키마 변경 시 영향 검토

401/403/입력 오류는 자동 재시도하지 않습니다. 429, 일시적 5xx, 네트워크 장애만 제한적으로 재시도하고, 응답을 잃은 POST는 원격 상태를 먼저 조회합니다. 토큰, 앱 시크릿, OAuth code를 로그에 남기지 않습니다.

월 1회와 배포 전에 [Threads changelog](https://developers.facebook.com/docs/threads/changelog), [게시 문서](https://developers.facebook.com/docs/threads/posts/), 실제 App Dashboard를 다시 확인합니다.

# 1. Threads API 개요

기본 API 호스트는 `https://graph.threads.net`입니다. 게시 자동화는 OAuth 사용자 토큰과 `threads_basic`, `threads_content_publish` 권한을 사용합니다.

핵심 흐름은 다음과 같습니다.

```text
사용자 동의 → 인증 코드 → 서버의 토큰 교환 → /me 계정 확인
                                              ↓
컨테이너 생성 → 처리 상태 확인 → 컨테이너 게시 → 원격 게시 ID 저장
```

컨테이너 ID를 받았다는 사실만으로 게시 성공이라고 판단하지 않습니다. 게시 응답의 원격 게시 ID와 후속 조회가 성공 증거입니다.

공식 근거와 GAP의 전체 목록은 [`../../reports/Threads 연동 설계.md`](../../reports/Threads%20연동%20설계.md)에 있습니다.

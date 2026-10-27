# 구조와 게시 흐름

```text
operator
  -> cli.py (입력 + --execute + --confirm)
  -> platform adapter (검증 + 공식 요청 생성)
  -> HttpTransport (30초 제한, JSON 검증, 예외 원인 로깅)
  -> official provider API
  -> provider object ID
```

`PublishRequest`는 플랫폼 중립 입력이고 각 어댑터가 플랫폼 계약을 책임집니다. `preview()`는 네트워크를 호출하지 않으며 인증 헤더를 `<redacted>`로 바꿉니다. `publish()`는 CLI가 두 확인 플래그를 검사한 뒤에만 호출됩니다.

플랫폼별 상태 흐름:

- Threads: 컨테이너 생성 → `threads_publish` → 게시물 ID.
- Instagram: 미디어 컨테이너 생성 → `media_publish` → 게시물 ID. 큰 영상의 비동기 상태 확인은 후속 범위입니다.
- Telegram: Bot API 전송 → `message_id`.
- TikTok: Creator Info 조회 → Direct Post 초기화 → `publish_id` 상태 조회 → 완료 상태.
- X: `POST /2/tweets` → Post ID.
- KakaoTalk: 나에게 메시지 → 성공 응답. 공개 피드 게시가 아닙니다.
- Naver 공유: 사용자 공유 화면 → 무인 실행 HOLD.
- Naver Cafe: OAuth 글쓰기 → `articleId`; 현재 텍스트·링크만 실행.
- Facebook Page: `/feed`, `/photos`, `/videos` → 객체 ID.
- LinkedIn: Posts API → 응답 헤더 `x-restli-id`; 미디어는 선업로드 URN 필요.
- Discord: 비밀 Webhook URL → 메시지 ID; 미리보기에서는 URL 전체를 가림.
- Reddit: OAuth `/api/submit` → 텍스트·링크 결과 ID.
- YouTube: Community 글쓰기 계약 없음, resumable 영상 업로더 미완성 → 실행 HOLD.

`capabilities.py`는 플랫폼의 공식 기능과 현재 로컬 구현 범위를 함께 보여줍니다. 두 값을 같은 것으로 간주하지 않습니다.

새 플랫폼은 `BaseAdapter`를 구현하고 `ADAPTERS`에 등록한 뒤, 엔드포인트·토큰 비노출·응답 ID 테스트를 추가합니다.

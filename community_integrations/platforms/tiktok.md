# TikTok 설정

1. TikTok for Developers에 앱을 등록하고 Content Posting API 제품을 추가합니다.
2. Direct Post를 활성화하고 `video.publish` 권한 승인을 받습니다.
3. 대상 사용자가 앱을 승인해 발급된 사용자 액세스 토큰을 `TIKTOK_ACCESS_TOKEN`에 설정합니다.
4. `PULL_FROM_URL`에 쓸 미디어 도메인/URL 접두사를 개발자 콘솔에서 검증합니다.
5. 감사되지 않은 클라이언트의 게시물은 비공개로 제한되므로 먼저 `SELF_ONLY`로 테스트합니다.
6. 서비스 목적을 공유 지침과 대조합니다. 개인 또는 내부 팀 계정만 관리하는 전용 업로더는 공식 지침의 허용 사례와 충돌할 수 있으므로 앱 감사 전에 HOLD합니다.

```powershell
python cli.py tiktok --text "영상 설명" --media-type VIDEO --media-url "https://verified.example.com/a.mp4"
```

응답의 `publish_id`는 완료된 게시물 ID가 아니라 비동기 작업 ID입니다. 실행 어댑터는 제한된 횟수만 상태를 조회하고 `PUBLISH_COMPLETE`가 확인되어야 성공으로 반환합니다.

공식 근거: [Direct Post 시작](https://developers.tiktok.com/docs/en/content-posting-api-get-started), [게시 상태 조회](https://developers.tiktok.com/docs/en/content-posting-api-reference-get-video-status), [공유 지침](https://developers.tiktok.com/docs/en/content-sharing-guidelines).

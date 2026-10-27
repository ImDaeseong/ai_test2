# X 설정

1. X Developer Console에서 Project와 App을 만듭니다.
2. OAuth 2.0 Authorization Code with PKCE 또는 OAuth 1.0a 사용자 컨텍스트를 설정하고 쓰기 권한을 부여합니다.
3. 사용자 액세스 토큰을 `X_USER_ACCESS_TOKEN`에 설정합니다.
4. Developer Console에서 선불 크레딧과 지출 한도를 확인합니다.

```powershell
python cli.py x --text "테스트"
```

2026-10-27 공식 가격 페이지 기준 Post 생성은 요청별 과금이며 URL 포함 생성은 단가가 다릅니다. 가격은 바뀔 수 있으므로 실제 전송 직전에 콘솔을 다시 확인하세요. 현재 어댑터는 텍스트/본문 URL을 지원하고, 미디어는 먼저 X Media Upload API로 올린 뒤 반환 ID를 Post에 연결하는 후속 범위입니다.

공식 근거: [Create Posts](https://docs.x.com/x-api/posts/create-post), [Upload media](https://docs.x.com/x-api/media/upload-media), [가격](https://docs.x.com/x-api/getting-started/pricing).

# 2. 앱 준비와 OAuth

## 준비 항목

1. Meta App Dashboard에서 앱을 만들고 Threads 사용 사례를 추가합니다.
2. OAuth Redirect URI, Deauthorize Callback URL, Data Deletion Requests URL을 등록합니다.
3. 첫 게시 예제에는 `threads_basic`, `threads_content_publish`만 요청합니다.
4. 브라우저에서 받은 authorization code는 서버에서 토큰으로 교환합니다. 앱 시크릿을 브라우저에 보내지 않습니다.
5. `/me`를 호출해 연결된 Threads 사용자 ID와 권한을 확인합니다.

## 환경변수

```text
THREADS_APP_ID=
THREADS_APP_SECRET=
THREADS_REDIRECT_URI=
THREADS_USER_ID=
THREADS_ACCESS_TOKEN=
```

실제 값은 `.env`, 문서, 로그, Git에 저장하지 않습니다. 이 예제는 `.env`를 자동으로 읽지 않습니다.

장기 사용자 토큰의 공식 예시 만료시간은 60일이며, 만료되지 않은 토큰은 `th_refresh_token` 흐름으로 갱신합니다. 앱 심사와 계정 유형의 정확한 요구사항은 실제 Dashboard에서 확인해야 하는 HOLD입니다.

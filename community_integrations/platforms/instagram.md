# Instagram 설정

1. 게시 대상 계정을 Instagram Professional(Business 또는 Creator)로 준비합니다. 개인 계정은 공식 게시 API 대상이 아닙니다.
2. Meta 앱을 만들고 Instagram 로그인/그래프 연동을 설정합니다.
3. 게시 권한(`instagram_content_publish` 또는 선택한 최신 로그인 방식의 동등 권한)을 승인받습니다.
4. Instagram 사용자 ID와 사용자 액세스 토큰을 `INSTAGRAM_USER_ID`, `INSTAGRAM_ACCESS_TOKEN`에 설정합니다.
5. 이미지·영상은 공개 HTTPS URL에 둡니다.

```powershell
python cli.py instagram --text "설명" --media-type IMAGE --media-url "https://example.com/a.jpg"
```

실제 실행은 컨테이너 생성 후 `media_publish`를 호출합니다. 큰 영상/Reels/Stories는 처리 시간이 걸릴 수 있으므로 운영 사용 전 컨테이너 상태 폴링을 추가하고 실제 계정에서 검증해야 합니다.

공식 근거: [Meta 공식 Instagram API Postman 컬렉션](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api).

# Facebook Page 설정

지원 범위는 Page 피드의 텍스트·링크·이미지·영상입니다. 음악 파일 단독 게시와 일반 파일 첨부는 이 어댑터 범위가 아닙니다. Reels는 별도 업로드·처리 흐름이 필요하므로 실제 계정 검증 전까지 HOLD입니다.

1. Meta 개발자 앱을 만들고 Facebook Login을 설정합니다.
2. 관리 대상 Page와 사용자에게 필요한 Page 게시 권한을 승인받습니다.
3. Page access token과 Page ID를 환경변수에 넣습니다.
4. 공개 HTTPS 이미지·영상 URL을 준비합니다.

```powershell
$env:FACEBOOK_PAGE_ID = "숫자 Page ID"
$env:FACEBOOK_PAGE_ACCESS_TOKEN = "Page access token"
python cli.py facebook_page --text "새 소식"
python cli.py facebook_page --text "사진 설명" --media-type IMAGE --media-url "https://example.com/photo.jpg"
```

Meta 개발자 문서는 조사 시점에 자동 열람 요청이 HTTP 429로 제한됐습니다. 따라서 엔드포인트 계약은 오프라인 테스트를 통과했지만 실제 Page 역할·권한·응답은 반드시 개발 Page에서 확인해야 합니다.

공식 진입점: [Pages API 문서](https://developers.facebook.com/docs/pages-api/), [Meta 공식 Postman](https://www.postman.com/meta/).

# Naver 설정과 서비스별 제한

Naver는 서비스를 나눠 판단해야 합니다.

- Blog: 로그인 방식 글쓰기 Open API가 2020-05-06 종료됨.
- Cafe: OAuth 기반 공식 글쓰기 API가 현재 문서화되어 있으며 텍스트와 multipart 이미지 첨부를 지원함.
- Cafe 앱 URL Scheme: 사용자가 앱에서 최종 작성하며 이미지·영상·파일 첨부 가능.
- Naver 공유하기: 사용자가 로그인·편집·전송하는 공유 화면.

```powershell
python cli.py naver --text "공유 제목" --title "공유 제목" --media-url "https://example.com/article"

$env:NAVER_ACCESS_TOKEN = "네이버 로그인 OAuth 토큰"
$env:NAVER_CAFE_ID = "카페 숫자 ID"
$env:NAVER_CAFE_MENU_ID = "게시판 숫자 ID"
python cli.py naver_cafe --title "카페 제목" --text "카페 본문"
```

`naver`는 공유 화면만 만들고 무인 실행을 차단합니다. `naver_cafe`는 텍스트·링크 글쓰기를 지원하며 공식 multipart 이미지 첨부는 후속 구현입니다. 아이디·비밀번호·쿠키·CAPTCHA·좌표 매크로 방식은 지원하지 않습니다.

공식 근거: [카페 글쓰기 API](https://developers.naver.com/docs/login/cafe-api/cafe-api.md), [카페 앱 URL Scheme](https://developers.naver.com/docs/utils/cafeapp/), [블로그 API 종료 공지](https://developers.naver.com/notice/article/7527), [네이버 공유하기](https://developers.naver.com/docs/share/navershare/).

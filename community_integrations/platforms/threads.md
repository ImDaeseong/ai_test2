# Threads 설정

1. Meta for Developers에서 Threads 사용 사례의 앱을 만듭니다.
2. OAuth 리디렉션 URI를 등록하고 `threads_basic`, `threads_content_publish` 권한을 요청합니다.
3. 사용자가 앱을 승인한 뒤 Threads 사용자 액세스 토큰과 사용자 ID를 받습니다.
4. `THREADS_USER_ID`, `THREADS_ACCESS_TOKEN` 환경변수를 설정합니다.
5. 텍스트는 바로 준비할 수 있고, 이미지·영상은 Meta 서버가 가져갈 수 있는 공개 HTTPS URL이 필요합니다.

```powershell
python cli.py threads --text "테스트"
python cli.py threads --text "테스트" --execute --confirm
```

이 어댑터는 컨테이너 생성 후 `threads_publish`를 호출합니다. 캐러셀·답글·설문·장문 첨부는 기존 [`../threads/`](../threads/) 학습 구현과 공식 최신 문서를 참고해 후속 확장합니다.

공식 근거: [Meta 공식 Threads API Postman 컬렉션](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api), [Meta 공식 예제 저장소](https://github.com/fbsamples/threads_api).

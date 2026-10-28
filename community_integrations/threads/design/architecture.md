# Threads 독립 연동 구조

```text
CLI/교육 UI
    │ PublishRequest
    ▼
ThreadsClient ── RequestBuilder
    │
    ├─ 컨테이너 생성
    ├─ 상태 조회
    └─ 게시
         │
         ▼
https://graph.threads.net
```

예제는 학습을 위해 요청 생성과 HTTP 실행만 분리합니다. 향후 통합 시에는 공통 `PublishRequest`와 채널별 `ThreadsAdapter` 사이에 경계를 두고, 큐·토큰 저장소·미디어 공개 URL·감사 증거를 별도 운영 구성요소로 추가합니다.

소비자 애플리케이션이 Threads 파라미터를 직접 만들지 않고 공통 게시 요청을 전달하도록 하는 것이 변경 격리의 핵심입니다.

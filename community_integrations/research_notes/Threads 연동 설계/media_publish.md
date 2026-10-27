# Threads API 콘텐츠 게시 지원과 절차

확인일: 2026-10-23 (Asia/Seoul)

## 어떤 콘텐츠를 게시할 수 있는가?

### Takeaway
공식 Threads API 게시 모델은 `TEXT`, `IMAGE`, `VIDEO`, `CAROUSEL`이다. 링크는 텍스트 게시물에 첨부하거나 본문의 첫 URL로 미리보기를 만들 수 있고, 답글과 인용은 각각 기존 게시물 ID를 컨테이너 생성 시 전달한다. 독립형 오디오/음악용 `media_type`이나 오디오 업로드 파라미터는 공식 게시 인터페이스에 없으며, 허용된 동영상 파일에 포함된 오디오 트랙만 동영상의 일부로 게시할 수 있다.

### Cited Findings
- 텍스트 게시물: `POST https://graph.threads.net/{threads-user-id}/threads`에 `media_type=TEXT`, `text`를 전달한다. 텍스트만 게시할 때 `text`는 `link_attachment`가 없으면 필수이며, 명시적 링크 첨부가 없으면 본문 첫 URL이 링크 미리보기에 사용된다. `link_attachment`는 텍스트 게시물에서만 사용할 수 있다. [Meta 공식 Threads API Postman 문서](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)
- 이미지 게시물: 같은 엔드포인트에 `media_type=IMAGE`, 공개 접근 가능한 `image_url`을 전달한다. `text`는 선택 사항이며 `alt_text`를 줄 수 있다. Meta 서버가 URL을 cURL로 가져가므로 로컬 파일 경로나 인증이 필요한 URL이 아니라 공개 서버 URL이어야 한다. [Meta 공식 Threads API Postman 문서](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)
- 동영상 게시물: `media_type=VIDEO`, 공개 `video_url`을 사용하며 `text`와 `alt_text`는 선택 사항이다. Meta가 URL에서 파일을 가져간다. [Meta 공식 Threads API Postman 문서](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)
- 캐러셀: 각 이미지/동영상 자식 컨테이너를 먼저 `is_carousel_item=true`로 만들고, 반환 ID 2–20개를 쉼표로 연결해 부모 컨테이너의 `media_type=CAROUSEL&children=...`에 전달한다. 이미지와 동영상을 혼합할 수 있다. [Meta 공식 Threads API Postman의 캐러셀 요청](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api?entity=request-34203612-ee0a2365-9d95-4cbe-8087-1cfb04d38c05)
- 답글: 새 컨테이너를 만들 때 `reply_to_id`에 답글 대상 Threads 게시물 ID를 전달한다. 이 파라미터는 텍스트·이미지·동영상·캐러셀 생성 요청에 제공된다. [Meta 공식 Threads API Postman 문서](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)
- 인용 게시물: 새 컨테이너 생성 시 `quote_post_id`에 인용할 Threads 게시물 ID를 전달한 뒤 일반 게시 단계로 발행한다. [Meta 공식 인용 게시물 컨테이너 요청](https://www.postman.com/meta/threads/request/eyal262/1-create-media-container); [Meta 공식 인용 게시물 발행 요청](https://www.postman.com/meta/threads/request/34203612-0944b188-4a57-4e68-a374-56c9e423acfb)
- 대체 텍스트: 단일 이미지/동영상 및 캐러셀의 각 자식 컨테이너에 `alt_text`를 전달할 수 있다. 캐러셀에서는 부모가 아니라 각 미디어 항목에 적용한다. [Meta 공식 Threads API Postman 문서](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)
- 독립 오디오/음악: 공식 컬렉션이 열거하는 단일 게시 컨테이너 유형은 text/image/video이고 캐러셀 항목도 image/video뿐이다. `AUDIO` 유형, `audio_url`, 음악 카탈로그 선택 또는 오디오 전용 업로드 요청은 공식 게시 컬렉션에 없다. 따라서 **독립 오디오/음악 업로드는 API 미지원으로 취급**해야 한다. [Meta 공식 단일 게시물 폴더](https://www.postman.com/meta/threads/folder/5zl9pf3/single-threads-posts); [Meta 공식 캐러셀 요청](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api?entity=request-34203612-ee0a2365-9d95-4cbe-8087-1cfb04d38c05)
- 영상 내 오디오는 별개다. Threads 게시 API는 동영상 파일 자체를 `video_url`에서 가져오므로, 지원 코덱으로 인코딩된 오디오 트랙이 영상 컨테이너 안에 포함된 경우 동영상의 일부로 게시된다. Meta 개발자 문서의 미디어 규격 원문 위치는 [Threads API 게시 문서](https://developers.facebook.com/docs/threads/posts/)이다.

### Inferences
- 제품 기능표에서는 “음악/오디오: 독립 업로드 불가, 오디오가 포함된 영상으로만 가능”이라고 두 칸으로 분리해야 한다. 소비자 Threads 앱에 음악 선택 기능이 존재하더라도 그것이 공개 API 기능임을 뜻하지 않는다.
- 링크 공유는 별도 `LINK` 미디어 유형이 아니라 `TEXT + link_attachment` 또는 텍스트 안 첫 URL 방식으로 구현해야 한다.
- 인용과 답글 모두 새 게시물의 컨테이너를 만드는 방식이므로, 원본을 수정하는 동작으로 설계하면 안 된다.

### Gaps
- Meta 개발자 문서(`developers.facebook.com`)는 조사 시점에 자동 열람 요청에 HTTP 429를 반환했다. 공식 Postman 컬렉션에는 게시 인터페이스가 확인되지만, 소비자 UI의 음악 기능과 API 간 차이를 명시적으로 설명하는 Meta 문장은 찾지 못했다.
- 공식 컬렉션에서 `alt_text` 파라미터 존재는 확인했지만 최대 길이는 해당 페이지에서 확인되지 않았다.

## 정확한 게시 순서와 상태 확인은 무엇인가?

### Takeaway
기본 흐름은 “공개 URL 준비 → 컨테이너 생성 → 처리 완료 확인 → 게시”다. 텍스트는 `auto_publish_text=true`로 게시 단계를 합칠 수 있지만, 이미지·동영상·캐러셀은 컨테이너 ID를 받은 뒤 준비 상태를 확인하고 `threads_publish`를 호출하는 흐름이 안전하다.

### Cited Findings
- 1단계 컨테이너 생성: `POST https://graph.threads.net/{threads-user-id}/threads`에 유형별 파라미터와 액세스 토큰을 전달하며 응답은 `{ "id": "<container-id>" }`다. [Meta 공식 Threads API Postman 문서](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)
- 2단계 게시: `POST https://graph.threads.net/{threads-user-id}/threads_publish?creation_id=<container-id>`를 호출하며 응답 ID는 게시된 Threads 게시물 ID다. [Meta 공식 발행 요청](https://www.postman.com/meta/threads/request/34203612-c940a17f-e719-4b5b-9d28-7390bc658fb7)
- 상태 조회: `GET https://graph.threads.net/<container-id>?fields=id,status,error_message`로 조회하며 상태는 `IN_PROGRESS`, `FINISHED`, `PUBLISHED`, `ERROR`, `EXPIRED`다. `FINISHED`가 게시 준비 완료이고, 24시간 안에 게시하지 않은 컨테이너는 `EXPIRED`가 된다. [Meta 공식 컨테이너 상태 요청](https://www.postman.com/meta/threads/request/m47wqlq/check-container-s-publishing-status)
- 텍스트는 생성 요청에 `auto_publish_text=true`를 넣어 별도 `threads_publish` 호출 없이 자동 게시할 수 있다. [Meta 공식 텍스트 컨테이너 요청](https://www.postman.com/meta/threads/request/jkuogpa/1-1-create-text-container)
- 캐러셀은 (1) 각 항목 컨테이너 생성, (2) 자식들이 준비될 때까지 상태 확인, (3) `children`으로 부모 캐러셀 컨테이너 생성, (4) 부모 상태 확인, (5) 부모 ID를 `threads_publish`에 전달하는 순서다. 자식은 직접 게시하지 않는다. [Meta 공식 Threads API Postman 문서](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api?entity=request-34203612-ee0a2365-9d95-4cbe-8087-1cfb04d38c05)
- 이미지와 동영상은 바이너리를 Graph API 요청 본문에 업로드하는 방식이 아니다. `image_url`/`video_url`이 공개 서버에 있어야 하며 Meta가 가져간다. [Meta 공식 단일 게시 문서](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api?entity=folder-34203612-995a4593-61de-4558-9b26-6c8becae85e4)

### Inferences
- 구현 시 `FINISHED`만 게시 가능 상태로 보고 지수 백오프 폴링을 하며, `ERROR`에서는 `error_message`를 보존하고 `EXPIRED`에서는 새 컨테이너를 생성하는 상태 머신이 적합하다.
- 공개 URL은 Meta 크롤러가 리다이렉트·인증·방화벽 없이 접근할 수 있어야 한다. 게시 완료 전 URL이 만료되지 않도록 충분한 TTL을 둬야 한다.

### Gaps
- 공식 상태 문서는 상태 값은 제공하지만 권장 폴링 간격·최대 재시도 횟수는 명시하지 않는다. 클라이언트 정책으로 정하고 rate-limit 응답을 존중해야 한다.
- 공식 Postman 상태 페이지 설명에는 상태 조회 URL이 `GET` 형태로 표시되지만 본문 한 줄에 `threads_publish`를 “check”에 사용한다고 적힌 문구가 있어 설명상 불일치가 있다. 실제 예시 URL과 필드 조회 방식(`GET /<container-id>?fields=...`)을 기준으로 구현해야 한다.

## 형식·크기 제약과 최종 지원표는 무엇인가?

### Takeaway
공식 게시 인터페이스로 확정되는 제약은 공개 URL, 캐러셀 2–20개, 이미지/동영상 항목 혼합, 유형별 필수 파라미터다. 아래의 세부 파일 규격은 Meta의 게시 문서에서 운영 시 다시 확인해야 하며, 이번 조사에서는 공식 개발자 페이지가 429여서 공식 원문을 직접 재독하지 못했다.

### Cited Findings
- Meta가 미디어 규격을 안내하는 공식 원문 진입점은 [Threads API 게시 문서](https://developers.facebook.com/docs/threads/posts/)이며, 공식 API 예제·파라미터는 [Meta 공식 Threads API Postman 컬렉션](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)에서 확인할 수 있다.
- 공식 컬렉션이 직접 확인해 주는 캐러셀 수량은 최소 2개, 최대 20개이며 이미지와 동영상을 혼합할 수 있다. [Meta 공식 캐러셀 요청](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api?entity=request-34203612-ee0a2365-9d95-4cbe-8087-1cfb04d38c05)

| 콘텐츠 | API 지원 | 핵심 생성 파라미터 | 외부 파일 전달 | 추가 게시 단계 | 비고 |
|---|---:|---|---|---|---|
| 글 | 예 | `media_type=TEXT`, `text` | 없음 | 예; `auto_publish_text=true`면 생략 가능 | 본문만 또는 링크 첨부 가능 |
| 링크 | 예 | `media_type=TEXT`, `link_attachment=<URL>` 또는 본문 첫 URL | 링크 URL | 텍스트와 동일 | 별도 `LINK` 유형 아님 |
| 단일 이미지 | 예 | `media_type=IMAGE`, `image_url`, 선택 `text`, `alt_text` | 공개 URL | 예 | URL에서 Meta가 가져감 |
| 캐러셀 | 예 | 자식별 IMAGE/VIDEO + `is_carousel_item=true`; 부모 `media_type=CAROUSEL`, `children` | 각 항목 공개 URL | 부모를 게시 | 2–20개, 혼합 가능 |
| 단일 동영상 | 예 | `media_type=VIDEO`, `video_url`, 선택 `text`, `alt_text` | 공개 URL | 예 | 처리 완료 폴링 필요 |
| 답글 | 예 | 위 유형 + `reply_to_id` | 유형에 따름 | 예 | 새 게시물로 생성 |
| 인용 | 예 | 위 유형 + `quote_post_id` | 유형에 따름 | 예 | 새 인용 게시물로 생성 |
| 독립 오디오/음악 파일 | **아니오** | 공식 `AUDIO`/`audio_url` 없음 | 해당 없음 | 해당 없음 | 소비자 UI 기능과 API 기능을 구분 |
| 오디오 포함 동영상 | 예 | `media_type=VIDEO`, `video_url` | 공개 동영상 URL | 예 | 오디오는 영상 파일의 트랙 |

### Inferences
- 운영 전 검증기의 초기 보수적 기준으로 이미지 JPEG/PNG, 최대 8MB와 동영상 MP4/MOV, 최대 1GB·5분을 고려할 수 있으나, 이는 이번 세션에서 Meta 원문을 직접 열어 재확인하지 못했으므로 배포 시 공식 [미디어 규격](https://developers.facebook.com/docs/threads/posts/)을 다시 읽고 상수화해야 한다.
- 업로드 모듈은 “Graph API로 파일 업로드”가 아니라 “임시 공개 스토리지에 올린 뒤 URL 전달”로 설계해야 한다.

### Gaps
- 이미지/동영상의 정확한 MIME, 코덱, 비트레이트, 프레임률, 해상도, 종횡비, 파일 크기 및 길이 제한은 공식 개발자 페이지의 429 때문에 이번 세션에서 원문 대조를 완료하지 못했다. 위 지원표는 공식 컬렉션으로 검증된 인터페이스 범위만 확정한다.
- 소비자 UI가 제공하는 음악 라이선스 카탈로그를 Threads API로 선택·첨부하는 공개 파라미터는 공식 컬렉션에서 발견되지 않았다. 향후 changelog에 `AUDIO`나 music attachment가 추가되는지 재검토해야 한다.

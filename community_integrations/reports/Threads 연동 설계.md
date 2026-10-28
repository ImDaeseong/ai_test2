# Threads 연동을 안전하게 재사용한다

**Threads의 공식 API만으로 글, 링크, 이미지, 동영상, 이미지·동영상 혼합 캐러셀, 답글과 인용 게시를 자동화할 수 있다. 그러나 독립 오디오·음악 파일을 게시하는 공식 `AUDIO` 유형은 확인되지 않았으므로, 음악은 오디오가 포함된 동영상이나 링크로만 다루는 것이 현재의 안전한 결론이다.** 인증은 OAuth 2.0 Authorization Code 흐름이고, 실제 게시물은 대부분 “미디어 컨테이너 생성 → 처리 상태 확인 → 게시”의 두 단계 계약을 따른다. 따라서 교육용 예제와 향후 소비자 애플리케이션 통합 모두에서 “요청 접수”와 “외부 게시 완료”를 분리해야 한다. 최소 구현은 텍스트 게시 한 건을 끝까지 통과시키는 세로 슬라이스로 시작하고, 이미지·동영상·캐러셀·인사이트·답글 관리는 검증된 권한과 상태 기계를 따라 순차적으로 추가하는 편이 안전하다. 토큰, 게시 작업, 원격 성공 증거, 삭제 작업을 서로 다른 수명주기로 관리하면 Threads 문서를 독립 교육 자료로 쓰면서도 이후 다른 커뮤니티 어댑터와 동일한 운영 계약으로 재사용할 수 있다. 이 보고서는 2026-10-23 확인 결과이며, Meta 개발자 문서 일부가 조사 중 HTTP 429를 반환해 직접 재검증하지 못한 항목은 **GAP**과 출시 **HOLD**로 남긴다.

## 공식 계약은 네 가지 게시 유형과 OAuth를 보장한다

**[검증됨]** Threads API의 기본 호스트는 `https://graph.threads.net`이며, Meta 앱에 Threads 사용 사례를 추가하고 사용자가 데이터 접근을 승인한 뒤 사용자 액세스 토큰으로 호출한다. OAuth 승인 코드는 서버에서 `POST /oauth/access_token`으로 교환하며 `client_id`, `client_secret`, `code`, `grant_type=authorization_code`, 승인 요청 때와 동일한 `redirect_uri`가 필요하다. 단기 사용자 토큰은 `grant_type=th_exchange_token`으로 장기 토큰과 교환할 수 있고, 공식 예시의 장기 토큰 유효시간은 **5,184,000초, 즉 60일**이다. 만료되지 않은 장기 토큰은 `GET /refresh_access_token?grant_type=th_refresh_token`으로 갱신한다. 앱 토큰은 별도 `client_credentials` 흐름으로 발급되므로 사용자 프로필 조회나 사용자 대신 게시하는 토큰의 대체재로 취급하면 안 된다. 토큰 디버거로 유형, 권한, 만료 여부를 확인하라는 절차도 공식 컬렉션에 포함되어 있다. ([Meta 공식 Threads API 문서](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)) ([Meta 공식 OAuth 요청 모음](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api?entity=folder-34203612-995a4593-61de-4558-9b26-6c8becae85e4))

**[검증됨]** 자기 프로필은 `GET /me?fields=id,username,name,threads_profile_picture_url,threads_biography` 형태로 확인할 수 있다. 초기 게시 기능에 필요한 최소 권한은 `threads_basic`과 `threads_content_publish`이고, 답글 읽기·관리와 인사이트에는 각각 `threads_read_replies`, `threads_manage_replies`, `threads_manage_insights`가 관련된다. 공식 컬렉션에는 검색, 멘션, 삭제, 위치 태그, 프로필 발견을 위한 추가 권한도 보이지만, 현재 UI에 기능이 없는 권한을 미리 요청할 이유는 없다. ([Meta 공식 프로필 요청](https://www.postman.com/meta/threads/request/q9os31a/get-threads-user-s-profile-information)) ([Meta 공식 Threads 요청 컬렉션](https://www.postman.com/meta/threads/request/u22r2j5/control-who-can-reply))

**[설계 권고]** 교육용 첫 장은 “Meta 앱 준비 → OAuth 연결 → `/me`로 연결 계정 확인 → 텍스트 게시 → 원격 게시 ID 저장”만 다루는 것이 좋다. 이 흐름은 사용자가 보는 화면, 서버의 토큰 교환, 외부 API 호출, 성공 증거 저장까지 전체 경계를 한 번에 보여 준다. 두 번째 장부터 장기 토큰 갱신, 이미지·동영상 공개 URL, 컨테이너 폴링, 캐러셀, 인사이트와 답글 관리를 추가하면 각 단계가 독립된 검증 과제가 된다. 브라우저는 OAuth 시작과 콜백 결과만 다루고, `client_secret`을 사용하는 코드 교환과 토큰 저장은 서버 책임으로 고정해야 한다.

**[GAP]** 실제 외부 사용자에게 필요한 App Review, Business Verification 또는 Tech Provider Verification의 정확한 조합은 조사 중 공식 Threads 본문을 직접 열지 못해 확정하지 않았다. 일반·크리에이터·비즈니스 계정 중 어떤 유형이 각 기능에 요구되는지도 공식 컬렉션만으로 단정할 수 없다. 따라서 실제 Meta App Dashboard의 `Required actions`, `App Review`, 권한별 접근 수준과 대상 계정의 OAuth 성공을 출시 전 증거로 남겨야 한다.

## 글·그림·영상은 게시되지만 음악은 영상으로 우회한다

**[검증됨]** 공식 게시 인터페이스의 핵심 유형은 `TEXT`, `IMAGE`, `VIDEO`, `CAROUSEL`이다. 링크는 별도 `LINK` 유형이 아니라 텍스트 게시물의 `link_attachment` 또는 본문의 첫 URL로 제공한다. 이미지와 동영상은 Graph API 요청에 바이너리를 직접 첨부하지 않고, Meta가 접근할 수 있는 공개 `image_url` 또는 `video_url`을 전달한다. 단일 이미지·동영상에는 `alt_text`를 지정할 수 있고, 캐러셀에서는 각 자식 항목에 대체 텍스트를 둔다. 답글은 `reply_to_id`, 인용은 `quote_post_id`를 새 컨테이너 생성 요청에 추가하는 방식이므로 원본 수정이 아니라 새 게시물 생성이다. ([Meta 공식 Threads API Postman 문서](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)) ([Meta 공식 인용 게시물 요청](https://www.postman.com/meta/threads/request/eyal262/1-create-media-container))

| 게시 목적 | 공식 API 지원 | 핵심 계약 | 구현 시 주의점 |
|---|---:|---|---|
| 글 | 예 | `media_type=TEXT`, `text` | `auto_publish_text=true` 단축 흐름 가능 |
| 링크 | 예 | `TEXT` + `link_attachment` 또는 본문 첫 URL | 별도 링크 미디어 유형이 아님 |
| 단일 그림 | 예 | `media_type=IMAGE`, 공개 `image_url` | Meta가 가져갈 때까지 URL 유지 |
| 단일 영상 | 예 | `media_type=VIDEO`, 공개 `video_url` | 비동기 처리 상태 확인 필요 |
| 캐러셀 | 예 | 자식 2–20개 생성 후 부모 `CAROUSEL` | 이미지·동영상 혼합 가능, 자식은 직접 게시하지 않음 |
| 답글·인용 | 예 | `reply_to_id` 또는 `quote_post_id` | 새 게시물로 발행 |
| 독립 음악·오디오 파일 | **확인되지 않음** | 공식 `AUDIO`·`audio_url` 없음 | 지원으로 표시하지 않음 |
| 오디오 포함 영상 | 예 | `VIDEO` 파일 내부 오디오 트랙 | 영상 규격과 저작권을 함께 검토 |

**[검증됨]** 캐러셀은 이미지·동영상 자식 컨테이너를 각각 `is_carousel_item=true`로 만든 뒤, 준비된 자식 ID **2–20개**를 부모 `media_type=CAROUSEL&children=...`에 전달하고 부모만 게시한다. 독립 음악 업로드를 위한 `AUDIO`, `audio_url`, 음악 카탈로그 선택 파라미터는 공식 게시 컬렉션에서 발견되지 않았다. 따라서 소비자 Threads 앱에 음악 선택 UI가 있다는 사실을 공개 API 능력으로 확대 해석해서는 안 된다. ([Meta 공식 캐러셀 요청](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api?entity=request-34203612-ee0a2365-9d95-4cbe-8087-1cfb04d38c05)) ([Meta 공식 단일 게시물 폴더](https://www.postman.com/meta/threads/folder/5zl9pf3/single-threads-posts))

**[설계 권고]** 미디어 모듈은 원본 파일 저장, 공개 전달 URL 발급, Threads 컨테이너 생성, 원격 fetch 완료까지를 하나의 수명주기로 다뤄야 한다. URL은 인증이나 사내 방화벽 없이 Meta 크롤러가 접근할 수 있어야 하며, 처리 완료 전에 만료되어서는 안 된다. 하지만 영구 공개 URL도 불필요하므로 게시 완료와 장애 재조정 시간을 포함하는 제한된 TTL을 두고 이후 폐기하는 편이 좋다. “음악 게시” 기능은 제품 문서에서 `독립 오디오: 미지원`, `오디오 포함 영상: 지원`, `음악 링크: 링크 게시로 지원`의 세 가지로 나눠야 사용자가 실제 능력을 오해하지 않는다.

**[GAP]** 이미지·동영상의 정확한 MIME, 코덱, 비트레이트, 프레임률, 해상도, 종횡비, 파일 크기·길이와 `alt_text` 최대 길이는 공식 게시 문서 본문을 429 때문에 직접 재검증하지 못했다. 보수적 상수를 사실처럼 고정하지 말고, 출시 직전 [Threads 게시 문서](https://developers.facebook.com/docs/threads/posts/)를 사람이 확인해 검증기와 테스트 fixture를 갱신해야 한다. 음악 저작권과 지역별 라이선스 역시 API 지원 여부와 별개의 법무 검토 대상이다.

## 컨테이너 상태가 게시 성공의 유일한 근거다

**[검증됨]** 표준 게시 순서는 `POST /{threads-user-id}/threads`로 컨테이너를 만들고, `GET /{container-id}?fields=id,status,error_message`로 준비 상태를 확인한 뒤, `POST /{threads-user-id}/threads_publish?creation_id={container-id}`로 발행하는 것이다. 생성 응답의 ID는 게시물 ID가 아니라 컨테이너 ID일 수 있으므로, ID 하나를 받았다는 이유만으로 게시 완료를 선언하면 안 된다. 공식 상태는 `IN_PROGRESS`, `FINISHED`, `PUBLISHED`, `ERROR`, `EXPIRED`이며, `FINISHED`가 게시 준비 완료다. 24시간 안에 게시하지 않은 컨테이너는 `EXPIRED`가 된다. 텍스트는 `auto_publish_text=true`로 생성과 게시를 합칠 수 있지만, 교육과 운영에서 성공 증거를 일관되게 다루려면 반환된 원격 게시 ID를 별도로 기록해야 한다. ([Meta 공식 컨테이너 상태 요청](https://www.postman.com/meta/threads/request/m47wqlq/check-container-s-publishing-status)) ([Meta 공식 발행 요청](https://www.postman.com/meta/threads/request/34203612-c940a17f-e719-4b5b-9d28-7390bc658fb7))

**[검증됨]** 게시 쿼터는 `GET /me/threads_publishing_limit`으로 조회할 수 있고, 게시물 인사이트는 `GET /{threads-media-id}/insights`에서 `views`, `likes`, `replies`, `reposts`, `quotes`, `shares` 같은 metric을 요청한다. 답글은 replies/conversation으로 읽고 `POST /{reply-thread-id}/manage_reply?hide=true|false`로 숨김 상태를 관리할 수 있으며, 공식 컬렉션에는 pending reply 승인·무시, 답글 작성과 답글 허용 대상 제어도 포함되어 있다. 웹훅 지원의 존재는 Meta 공식 샘플 저장소와 Threads Webhooks 문서 진입점에서 확인된다. ([Meta 공식 게시 한도 요청](https://www.postman.com/meta/threads/request/34203612-f4590341-9bee-44f5-901b-606078a03c96)) ([Meta 공식 Get Post Insights](https://www.postman.com/meta/threads/request/434u2bd/get-post-insights)) ([Meta 공식 Graph API Webhooks Samples](https://github.com/fbsamples/graph-api-webhooks-samples))

**[설계 권고]** 재사용 가능한 내부 계약은 커뮤니티 공통 모델과 Threads 어댑터를 분리해야 한다. 공통 `PublishRequest`에는 `id`, `channel`, `account_id`, 정규화된 콘텐츠, `media_refs`, `scheduled_at`, `idempotency_key`를 두고, 실행별 `PublishAttempt`에는 `request_id`, `attempt_no`, `state`, `provider_container_id`, `provider_post_id`, `provider_trace_id`, 정규화 오류와 시각을 둔다. 상태는 `DRAFT → QUEUED → CREATING_CONTAINER → PROCESSING → PUBLISHING → PUBLISHED`를 기본 경로로, `REAUTH_REQUIRED`, `FAILED_PERMANENT`, `CANCELLED`, `HOLD`를 중단 상태로 사용한다. 이 모델이면 향후 소비자 애플리케이션은 공통 요청만 만들고, Threads 어댑터가 URL 전달·컨테이너·상태를 책임진다.

```text
교육 UI 또는 소비자 애플리케이션
        │  공통 PublishRequest
        ▼
게시 오케스트레이터 ── outbox/queue ── Threads worker
        │                                │
        │                                ├─ OAuth/token vault
        │                                ├─ media URL provider
        │                                └─ graph.threads.net adapter
        ▼
작업·시도·증거 저장소 ◀── 상태/원격 ID/오류/trace
        │
        ├─ insights reader
        ├─ webhook inbox + reconciliation
        └─ deletion/compliance workflow
```

**[설계 권고]** 원격 호출의 성공 증거는 provider post ID, API 응답 시각, 컨테이너 최종 상태, 가능하면 게시물 재조회 또는 permalink로 구성한다. 인사이트는 게시 성공과 별개의 읽기 파이프라인으로 저장하고 metric별 `observed_at`을 둔다. 누락 metric을 0으로 변환하면 “데이터 없음”과 “실제 0”을 구분할 수 없으므로 그대로 보존한다. 답글 자동 숨김·승인은 오탐의 외부 영향이 크므로 첫 버전은 사람 승인 큐를 기본값으로 두고, 웹훅은 최종 진실이 아니라 재조회 신호로 취급해야 한다.

**[GAP]** 공식 Threads Webhooks 본문은 조사 시 429를 반환해 현재 구독 필드, 서명 헤더, 재전송 기간을 직접 검증하지 못했다. 웹훅을 핵심 동기화 경로로 쓰기 전에 실제 앱의 테스트 이벤트로 서명, 중복, 지연, 순서 뒤바뀜과 재전송을 검증해야 한다. 그전까지는 API 재조회와 주기적 reconciliation이 기준 경로다.

## 보안·재시도·HOLD가 상용화 경계를 만든다

**[검증됨]** Meta Platform Terms는 정당한 사업 목적에 더 이상 필요하지 않은 Platform Data, 서비스 종료 시의 데이터, Meta나 사용자가 삭제를 요청한 데이터, 사용자가 계정을 닫은 경우의 데이터를 가능한 한 신속히 삭제하도록 요구한다. 사용자가 데이터 수정·삭제를 요청할 수 있는 명확하고 쉽게 접근 가능한 방법도 필요하다. Threads 앱 설정에는 OAuth Redirect URI 외에 Deauthorize Callback URL과 Data Deletion Requests URL이 들어간다. ([Meta Platform Terms](https://developers.facebook.com/terms/)) ([Threads 앱 생성 안내](https://developers.facebook.com/docs/threads/get-started/create-an-app))

**[설계 권고]** 자격 증명 저장소는 게시물·인사이트 저장소와 논리적으로 분리하고, 토큰은 KMS 또는 운영체제 비밀 저장소로 암호화한다. 게시 worker만 복호화 권한을 가지며 토큰, 앱 시크릿, OAuth code는 로그·큐 payload·오류 화면에서 마스킹한다. `state`는 일회성·짧은 TTL로 검증하고 redirect URI는 정확히 allowlist한다. 연결 해제나 삭제 요청은 단순히 계정을 `inactive`로 바꾸는 것이 아니라 데이터베이스, 큐, 캐시, 검색 인덱스, 백업 정책과 외부 처리자까지 추적하는 삭제 workflow로 만든다. 법적 보존 예외가 있으면 근거와 범위를 기록하고, 삭제 증거가 모이기 전에는 완료 처리하지 않는다.

**[설계 권고]** 오류는 `AUTH`, `PERMISSION`, `VALIDATION`, `RATE_LIMIT`, `TRANSIENT_PROVIDER`, `PROCESSING_FAILED`, `UNKNOWN_OUTCOME`으로 정규화한다. 401·403·검증 오류는 자동 반복하지 않고 재인증·권한·입력 수정 HOLD로 보낸다. 429, 일시적 5xx와 네트워크 오류만 제한된 지수 백오프와 지터로 재시도하며 공급자가 주는 대기·사용량 헤더를 우선한다. Meta Graph API는 한도 도달 뒤 계속 호출하면 복구가 늦어질 수 있으므로 호출을 멈추고 사용량 헤더와 오류 코드를 확인하라고 안내한다. 오류의 `message`, `type`, `code`, `error_subcode`, `fbtrace_id`는 비밀을 제거한 뒤 저장해야 공급자 지원과 사후 진단이 가능하다. ([Meta Graph API Rate Limits](https://developers.facebook.com/docs/graph-api/overview/rate-limiting/))

**[설계 권고]** 게시 POST의 공급자 측 idempotency key 보장은 확인되지 않았다. 그러므로 내부 `idempotency_key`에 unique constraint를 두고 계정별 동일 작업을 직렬화하며, 응답이 유실된 `UNKNOWN_OUTCOME`에서는 POST를 즉시 반복하지 말고 저장된 컨테이너 ID와 원격 게시 상태를 먼저 재조정한다. 사용자의 승인·예약 저장과 enqueue는 outbox 트랜잭션으로 묶고 worker lease와 조건부 상태 전이로 동시 실행을 막는다. 실패 작업은 DLQ로 보내되 사람이 재처리하기 전에 원격 결과를 조회한다.

다음 HOLD는 기능 체크박스가 아니라 출시 판정 계약이다. **`HOLD-META-APP`**은 앱 생성, 실제 callback URL 등록, 권한 승인과 Live/Published 상태의 대시보드 증거가 없을 때 유지한다. **`HOLD-LIVE-OAUTH`**는 실제 테스트 사용자의 동의, 토큰 교환, 권한·만료 조회와 로그 비밀 마스킹이 검증될 때까지 유지한다. **`HOLD-LIVE-PUBLISH`**는 텍스트 한 건과 지원할 각 미디어 유형이 컨테이너 생성부터 원격 조회까지 성공하기 전에는 해제하지 않는다. **`HOLD-WEBHOOK-CONTRACT`**은 현재 이벤트 필드·서명·재전송을 실제 payload로 확인하기 전까지 유지한다. **`HOLD-POLICY`**는 개인정보 처리방침, 삭제 경로, 보존표, 하위 처리자, 사고 대응과 콘텐츠·저작권 정책을 법무·보안·운영 담당자가 승인할 때까지 유지한다. **`HOLD-CHANGE`**는 changelog나 실제 응답 schema가 fixture와 달라졌을 때 영향 분석과 회귀 검증이 끝날 때까지 유지한다.

**[GAP]** 최신 게시·답글·검색의 정확한 숫자 한도, Graph API 전체 호출 예산, 공식 장애 SLA와 상태 알림 채널은 이번 조사에서 검증하지 못했다. 숫자를 코드에 하드코딩하지 말고 `threads_publishing_limit`, 실제 오류·사용량 응답, App Dashboard를 진실의 원천으로 사용해야 한다. 공식 Postman 컬렉션도 최신 기능을 모두 담지 못할 수 있다고 경고하므로, 월 1회와 배포 전에 [Threads Changelog](https://developers.facebook.com/docs/threads/changelog)를 확인하고 계약 smoke test와 저장된 응답 fixture의 schema 테스트를 실행해야 한다. ([Meta 공식 Threads API 컬렉션](https://www.postman.com/meta/threads/collection/dht3nzz/threads-api))

## 교육 자료와 공통 플랫폼은 같은 계약을 공유한다

**[설계 권고]** 독립 문서의 권장 순서는 “지원 범위와 비지원 음악 → 앱·OAuth 준비 → 최소 텍스트 게시 → 이미지·동영상 URL 전달 → 컨테이너 상태 기계 → 캐러셀 → 운영 오류·삭제·HOLD → 선택 기능인 인사이트·답글·웹훅”이다. 각 장은 요청 예시뿐 아니라 성공 증거와 실패 상태를 함께 보여 줘야 한다. 이렇게 구성하면 독자는 단순 curl 복사가 아니라 외부 시스템 연동에서 무엇을 완료로 볼지 배울 수 있고, 같은 자료를 이후 다른 커뮤니티 연동의 템플릿으로 사용할 수 있다.

**[설계 권고]** 코드 구조는 공통 도메인과 채널별 구현을 분리하는 정도면 충분하다. `core`에는 `PublishRequest`, `PublishAttempt`, 상태·오류·증거 계약을, `providers/threads`에는 OAuth, profile, publisher, insights, replies, webhook adapter를, `media`에는 임시 URL과 검증을, `operations`에는 queue, reconciliation, deletion, audit를 둔다. 문서와 테스트 fixture는 `docs/threads`와 `tests/contracts/threads`에 둔다. 처음부터 모든 커뮤니티의 최소공배수를 추상화하지 말고, Threads의 실제 세로 슬라이스가 통과한 뒤 두 번째 커뮤니티에서 반복되는 계약만 공통화해야 과도한 추상화를 피할 수 있다.

**[검증됨]** Meta 공식 자료는 Threads Postman 컬렉션이 시간에 따라 갱신되지만 최신 기능 전부가 들어 있지 않을 수 있으므로 개발자 changelog를 기준으로 보라고 명시한다. 이는 교육 자료에도 “확인일”과 “검증 근거”가 필요하다는 뜻이다. API 요청 예제, 검증된 응답 fixture, 마지막 확인일, 미검증 GAP을 함께 버전 관리해야 책의 내용과 실제 구현이 서로 다른 시점의 API를 설명하는 문제를 줄일 수 있다. ([Meta 공식 Threads API 문서](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api))

## Conclusion

Threads 연동의 핵심은 게시 호출 자체가 아니라 **지원 범위를 정직하게 제한하고, 외부 성공을 증거로 확정하며, 바뀌는 API와 정책을 HOLD로 통제하는 것**이다. 이 원칙을 공통 계약으로 두면 교육 예제는 단순하고 설명 가능하게 유지되고, 향후 소비자 애플리케이션은 Threads의 세부 OAuth·컨테이너·재시도 규칙을 알지 않고도 동일한 게시 요청과 결과 모델을 사용할 수 있다.

첫 구현의 완료 조건은 텍스트 게시 코드가 존재하는 것이 아니라, 실제 OAuth 사용자로 `/me`를 확인하고 텍스트를 게시한 뒤 원격 게시 ID와 조회 증거를 저장하며, 토큰이 로그에 남지 않고, 실패 시 잘못된 자동 재시도를 하지 않는 것이다. 이미지·동영상·캐러셀과 운영 자동화는 이 기준을 유지한 채 한 종류씩 추가해야 한다. 음악, 웹훅 세부 계약, 미디어 정확 규격, 심사 조건처럼 이번 조사에서 확정하지 못한 영역은 문서의 약점이 아니라 다음 검증을 멈추지 않게 만드는 명시적 경계다.

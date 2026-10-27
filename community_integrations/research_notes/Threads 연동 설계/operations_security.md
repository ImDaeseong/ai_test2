# Threads API 운영·보안 최소 설계 노트

확인일: **2026-10-23 (Asia/Seoul)**
범위: 독립형 교육·참조 자료. 구현 명세가 아니라, 최소 통합 서비스가 지켜야 할 경계와 출시 전 확인 항목을 정리한다. 아래에서 **공식 요구/확인 사실**과 **설계 권고**를 구분한다.

## 1. 보안 경계와 데이터 수명주기

### Takeaway
OAuth 사용자 동의와 최소 권한이 신뢰 경계의 시작이며, 토큰·앱 시크릿·Threads 사용자 데이터는 게시 콘텐츠 자체와 분리해 보호해야 한다. 연결 해제나 삭제 요청은 단순 UI 상태 변경이 아니라 저장 데이터와 하위 처리자의 삭제까지 추적하는 운영 절차여야 한다.

### Cited Findings
- **공식 요구/확인 사실:** Meta의 공식 Threads Postman 문서는 Meta 앱에 Threads 사용 사례를 추가하고, 사용자가 앱의 데이터 접근을 승인하도록 하며, OAuth Authorization Code로 코드를 토큰과 교환하도록 안내한다. 교환 시 `redirect_uri`는 승인 요청 때 사용한 값과 같아야 한다. [Meta 공식 Threads API 문서](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api) (확인: 2026-10-23)
- **공식 요구/확인 사실:** 공식 문서가 열거하는 관련 권한은 `threads_basic`, `threads_content_publish`, `threads_read_replies`, `threads_manage_replies`, `threads_manage_insights`이며, 토큰 디버거로 권한과 만료 여부를 확인할 수 있다. 권한은 기능별로 요청해야 한다. [Meta 공식 Threads API 문서](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api?entity=folder-34203612-995a4593-61de-4558-9b26-6c8becae85e4) (확인: 2026-10-23)
- **공식 요구/확인 사실:** 단기 토큰은 `/access_token?grant_type=th_exchange_token`으로 장기 토큰으로 교환하며, 공식 예시 응답의 `expires_in`은 5,184,000초이다. 만료되지 않은 장기 토큰은 `/refresh_access_token?grant_type=th_refresh_token`으로 갱신한다. [Meta 공식 Threads API Authorization](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api?entity=folder-34203612-995a4593-61de-4558-9b26-6c8becae85e4) (확인: 2026-10-23)
- **공식 요구/확인 사실:** Meta Platform Terms는 Platform Data를 정당한 사업 목적에 더 이상 필요하지 않을 때, 서비스 종료 시, Meta 또는 사용자가 요청할 때, 사용자가 계정을 닫을 때, 법률상 요구될 때 가능한 한 신속히 삭제하도록 요구한다. 사용자가 수정·삭제를 요청할 수 있는 명확하고 쉽게 접근 가능한 방법도 요구한다. [Meta Platform Terms](https://developers.facebook.com/terms/) (확인: 2026-10-23; 공식 페이지는 조사 도구에서 429/접근 제한이 있어 검색 캐시로 조항을 대조함)
- **공식 요구/확인 사실:** Meta의 앱 설정 안내에는 OAuth Redirect URI 외에 사용자가 앱 연결을 해제할 때 호출되는 Deauthorize Callback URL과 Data Deletion Requests URL이 포함된다. [Threads 앱 생성 안내](https://developers.facebook.com/docs/threads/get-started/create-an-app) (확인: 2026-10-23; 공식 페이지 직접 본문 접근 제한, 공식 URL을 인용한 문서 사본과 검색 결과로 확인)

### Inferences
- **설계 권고:** `credential` 저장소를 게시물·분석 데이터 저장소와 논리적으로 분리하고, 토큰은 애플리케이션 로그·작업 payload·오류 응답에 남기지 않는다. 저장 시 KMS/OS 비밀 저장소로 암호화하고 복호화 권한은 게시 worker에만 준다.
- **설계 권고:** 토큰 레코드는 `account_id`, 권한 집합, 발급/만료 시각, 마지막 검증 시각, 상태(`ACTIVE`, `REAUTH_REQUIRED`, `REVOKED`, `DELETION_PENDING`)만 노출한다. 실제 토큰 값은 별도 암호문 필드에 저장한다.
- **설계 권고:** OAuth `state`를 일회성·짧은 TTL로 검증하고, 콜백의 redirect URI를 정확히 allowlist한다. 요청 권한은 현재 활성 기능에 필요한 것만 사용한다.
- **설계 권고:** 연결 해제/삭제 요청은 데이터베이스, 큐, 캐시, 검색 인덱스, 백업 정책, 외부 처리자를 포괄하는 삭제 작업으로 만들고 `requested_at`, 대상, 단계별 결과, 완료 증거를 기록한다. 법적 보존 예외가 있으면 근거와 범위를 별도 기록하고 자동 완료하지 않는다.

### Gaps
- 정확한 App Review/Business Verification 조건은 요청 권한과 앱 배포 상태에 따라 달라질 수 있으므로 실제 Meta App Dashboard에서 출시 직전 확인해야 한다.
- 조직의 개인정보 처리방침, 보존 기간, 사고 통지 절차가 한국 개인정보보호법 및 서비스 대상 지역 법률을 충족하는지는 법무 검토 대상이다.

## 2. 통합 계약: 게시, 상태, 인사이트, 답글, 웹훅

### Takeaway
내부 계약은 “요청 접수”와 “Threads 게시 완료”를 분리해야 한다. API가 반환한 원격 ID와 후속 상태 조회가 있어야 성공으로 확정하며, 인사이트·답글 관리·웹훅은 별도 권한과 기능 플래그로 격리한다.

### Cited Findings
- **공식 요구/확인 사실:** Meta 공식 컬렉션은 텍스트·단일 이미지·비디오·캐러셀 게시를 지원하고, 생성된 Threads 미디어 컨테이너 ID를 후속 요청에 사용한다. 텍스트는 `auto_publish_text=true`로 생성과 동시에 게시할 수도 있다. [Meta 공식 Threads API 문서](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api) (확인: 2026-10-23)
- **공식 요구/확인 사실:** 컨테이너 상태 확인 요청은 `GET /{container_id}?fields=id,status,error_message` 형태다. 따라서 컨테이너 생성 성공만으로 최종 게시 성공을 뜻하지 않는다. [Meta 공식 Check Container Status](https://www.postman.com/meta/threads/request/m47wqlq/check-container-s-publishing-status) (확인: 2026-10-23)
- **공식 요구/확인 사실:** 게시 쿼터는 `GET /me/threads_publishing_limit`으로 조회할 수 있다. [Meta 공식 Retrieve Publishing Quota Limit](https://www.postman.com/meta/threads/request/34203612-f4590341-9bee-44f5-901b-606078a03c96) (확인: 2026-10-23)
- **공식 요구/확인 사실:** 게시물 인사이트는 `GET /{threads-media-id}/insights`이며 공식 예시 metric에는 `views`, `likes`, `replies`, `reposts`, `quotes`, `shares`가 있다. `threads_manage_insights` 권한이 관련된다. [Meta 공식 Get Post Insights](https://www.postman.com/meta/threads/request/434u2bd/get-post-insights) (확인: 2026-10-23)
- **공식 요구/확인 사실:** 답글은 replies/conversation으로 읽고, `POST /{reply_thread_id}/manage_reply?hide=true|false`로 숨김/복원을 수행할 수 있다. 공식 컬렉션에는 pending replies 조회와 `manage_pending_reply?approve=true|false`, 답글 작성, 답글 허용 대상 제어도 포함되어 있다. [Meta 공식 Threads API 문서](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api?entity=request-34203612-74fb48b1-ad1a-480e-b200-4dcdb8126a2f) (확인: 2026-10-23)
- **공식 요구/확인 사실:** Meta가 유지하는 샘플 저장소는 Threads Webhooks 공식 문서를 명시적으로 연결하며 Threads 웹훅 지원의 존재를 확인시킨다. [Meta 공식 Graph API Webhooks Samples](https://github.com/fbsamples/graph-api-webhooks-samples) 및 [Threads Webhooks](https://developers.facebook.com/docs/threads/webhooks) (확인: 2026-10-23)
- **공식 요구/확인 사실:** Meta 공식 Postman 컬렉션 자체도 최신 기능이 모두 반영되지 않을 수 있으므로 Threads changelog를 최신 기준으로 보라고 경고한다. [Meta 공식 Threads API 문서](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api) 및 [Threads Changelog](https://developers.facebook.com/docs/threads/changelog) (확인: 2026-10-23)

### Inferences
- **설계 권고:** 내부 최소 계약을 다음처럼 고정한다: `PublishRequest(id, account_id, content, media_refs, scheduled_at, idempotency_key)` → `PublishAttempt(request_id, attempt_no, state, container_id, remote_post_id, error_class, provider_trace_id, timestamps)`.
- **설계 권고:** 상태 기계는 `DRAFT → QUEUED → CREATING_CONTAINER → PROCESSING → PUBLISHING → PUBLISHED`와 종결/중단 상태 `FAILED_PERMANENT`, `REAUTH_REQUIRED`, `CANCELLED`, `HOLD`를 둔다. `container_id`만 받은 경우 `PUBLISHED`로 전환하지 않는다.
- **설계 권고:** 성공 증거는 원격 게시 ID, API 응답 시각, 컨테이너 최종 상태, 가능하면 permalink 조회 결과로 구성한다. 콘텐츠 본문 전체나 토큰은 감사 로그에 복제하지 않는다.
- **설계 권고:** 인사이트는 게시 경로와 분리된 읽기 작업으로 처리하고, metric별 `observed_at`을 저장한다. 누락된 metric을 0으로 치환하지 않는다.
- **설계 권고:** 답글 자동 숨김·승인은 오탐의 외부 영향이 크므로 초기 버전은 사람 승인 큐를 기본값으로 한다. 원격 성공 응답을 받은 뒤에만 로컬 moderation 상태를 확정한다.
- **설계 권고:** 웹훅은 “알림”으로 취급하고 원격 객체를 API로 재조회해 현재 상태를 확정한다. 중복·지연·순서 뒤바뀜을 허용하며 이벤트 ID 또는 안정적인 payload 해시로 중복 제거한다.

### Gaps
- 2026-10-23 조사 시 공식 Threads Webhooks 페이지가 429로 본문을 반환하지 않아, 현재 구독 가능한 정확한 필드 목록·서명 헤더·재전송 시간은 직접 검증하지 못했다. 이 값들은 구현에 하드코딩하지 말고 출시 전 공식 페이지와 실제 테스트 payload로 확인해야 한다.
- 음악 파일의 직접 업로드 지원은 이번 공식 계약 조사에서 확인되지 않았다. ‘음악 게시’는 비디오에 포함된 오디오, 링크 공유, 별도 저작권/라이선스 문제를 각각 검토하고 지원 확인 전에는 범위 밖으로 둔다.

## 3. 오류·재시도, 변경 대응, 정책·운영 HOLD

### Takeaway
재시도는 전송 실패가 아니라 “원격 결과를 모르는 상태”를 다루는 절차다. 중복 게시를 피하려면 재전송 전에 컨테이너/원격 ID를 조회하고, 권한·심사·정책·웹훅 계약처럼 외부에서 결정되는 조건은 증거가 있을 때까지 HOLD로 유지해야 한다.

### Cited Findings
- **공식 요구/확인 사실:** Meta Graph API의 모든 요청에는 rate limit이 적용될 수 있고, 한도 도달 뒤 계속 호출하면 복구 시간이 늘어날 수 있으므로 호출을 멈추고 사용량 헤더 및 오류 코드를 확인하라고 안내한다. [Meta Graph API Rate Limits](https://developers.facebook.com/docs/graph-api/overview/rate-limiting/) (확인: 2026-10-23)
- **공식 요구/확인 사실:** Meta Graph API 오류 예시는 `message`, `type`, `code`, `fbtrace_id`를 포함한다. `fbtrace_id`는 공급자 지원과 진단을 위해 보존할 가치가 있다. [Meta Graph API Rate Limits](https://developers.facebook.com/docs/graph-api/overview/rate-limiting/) (확인: 2026-10-23)
- **공식 요구/확인 사실:** Threads 공식 컬렉션은 토큰의 권한·만료 검증, 컨테이너 상태 조회, 게시 쿼터 조회를 Troubleshooting/Authorization 흐름으로 제공한다. [Meta 공식 Threads API 문서](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api) (확인: 2026-10-23)
- **공식 요구/확인 사실:** 공식 Threads Postman 자료는 컬렉션이 최신 기능 전부를 보여주지 않을 수 있음을 명시하므로 changelog 감시가 필요하다. [Meta 공식 Threads API 문서](https://www.postman.com/meta/threads/collection/dht3nzz/threads-api) 및 [Threads Changelog](https://developers.facebook.com/docs/threads/changelog) (확인: 2026-10-23)

### Inferences
- **설계 권고 — 오류 분류:** `AUTH`(401/토큰 만료·취소), `PERMISSION`(403/권한 부족), `VALIDATION`(잘못된 요청·미지원 미디어), `RATE_LIMIT`, `TRANSIENT_PROVIDER`(5xx/timeout), `PROCESSING_FAILED`(컨테이너 최종 오류), `UNKNOWN_OUTCOME`(응답 전 연결 단절)로 정규화한다. 원본 HTTP status, Meta error code/subcode/type/message, `fbtrace_id`는 비밀을 제거해 저장한다.
- **설계 권고 — 재시도:** `RATE_LIMIT`과 일시적 5xx/네트워크 오류만 지수 백오프+지터와 작은 최대 횟수로 재시도한다. 401/403/검증 오류는 자동 반복하지 않고 재인증·권한·입력 수정 HOLD로 보낸다. 사용량/Retry-After 계열 헤더가 있으면 우선한다.
- **설계 권고 — 중복 방지:** 내부 `idempotency_key`에 unique constraint를 두고 계정별 동일 작업을 직렬화한다. 응답 유실 뒤에는 저장된 `container_id`의 상태와 원격 게시 기록을 먼저 조회한다. 공급자가 게시 생성의 idempotency key를 공식 보장한다는 근거는 확인되지 않았으므로, 단순 POST 재전송을 안전하다고 가정하지 않는다.
- **설계 권고 — 큐:** outbox 트랜잭션으로 사용자 승인/예약 저장과 작업 enqueue를 원자화한다. worker lease와 상태 전이를 조건부 업데이트하여 동시 실행을 막는다. 실패 작업은 DLQ에 보내되 수동 재처리 전 원격 결과를 재조정한다.
- **설계 권고 — 관측성:** 계정·작업·시도 단위 correlation ID, 단계별 지연, 상태 전이, HTTP status, 정규화 오류, provider trace ID, 쿼터 관측치를 기록한다. 토큰, app secret, OAuth code, 원문 개인정보는 로그에서 마스킹한다.
- **설계 권고 — 변경 대응:** API host/version, 권한, 지원 media/metric, webhook field를 adapter 뒤에 둔다. 월 1회 및 배포 전 changelog 확인, 공식 Postman 계약 smoke test, 저장된 fixture에 대한 schema 호환성 테스트를 실행한다. 알 수 없는 필드는 무시하되 필수 필드 누락은 경고와 HOLD로 처리한다.

### Gaps / 출시 HOLD
- **HOLD-META-APP:** Meta 앱 생성, 실제 Redirect URI/Deauthorize/Data Deletion URL 등록, 필요한 권한 승인 및 앱의 실제 Live/Published 상태를 대시보드 캡처나 내보낸 설정으로 확인하기 전에는 외부 사용자 사용 가능으로 표시하지 않는다.
- **HOLD-LIVE-OAUTH:** 테스트 사용자의 실제 OAuth 동의, 토큰 교환, 권한/만료 조회가 성공하고 비밀이 로그에 남지 않았다는 증거가 없으면 인증 완료로 표시하지 않는다.
- **HOLD-LIVE-PUBLISH:** 텍스트 1건과 사용하려는 각 미디어 유형에 대해 실제 컨테이너 생성→상태 확인→게시→원격 조회가 성공하기 전에는 게시 기능을 완료 처리하지 않는다. 실제 게시에는 사용자 승인과 콘텐츠 검토가 필요하다.
- **HOLD-WEBHOOK-CONTRACT:** 공식 웹훅 필드·서명 검증·재전송 동작을 현재 문서와 실제 테스트 이벤트로 확인하기 전에는 webhook 기반 동기화를 신뢰 경로로 사용하지 않는다. 그 전에는 명시적 조회/재조정이 기준이다.
- **HOLD-POLICY:** 개인정보 처리방침, 데이터 삭제 경로, 보존표, 하위 처리자 목록, 사고 대응, 콘텐츠/저작권 정책을 사람(법무·보안·운영)이 승인하기 전에는 상용 출시 완료로 표시하지 않는다.
- **HOLD-CHANGE:** Threads changelog 또는 실제 응답 schema가 계약 fixture와 달라지면 자동 적응을 가장해 통과시키지 않고, 영향 분석·테스트·사람 승인 후 해제한다.

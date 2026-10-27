# Threads API 인증·권한·앱 설정·운영 수명주기

확인일: 2026-10-23 (Asia/Seoul). 이 문서는 Meta가 운영하는 공식 Threads Postman 워크스페이스와 Meta 공식 정책·제품 문서만 사실 근거로 사용한다. `developers.facebook.com/docs/threads/` 본문은 확인 시점에 자동 요청이 HTTP 429를 반환했으므로, 그 페이지의 세부 내용을 추정해 채우지 않았다.

## 어떤 공식 API와 엔드포인트로 프로필을 읽고 글을 게시하는가?

### Takeaway
Threads API는 `https://graph.threads.net`에서 OAuth 2.0 사용자 토큰으로 호출하는 Graph API다. 최소 구현은 `/me` 프로필 확인과 `/{threads-user-id}/threads` 컨테이너 생성, `/{threads-user-id}/threads_publish` 게시의 두 단계이며, 공식 컬렉션은 텍스트 게시에 한해 `auto_publish_text=true` 단축 흐름도 제시한다.

### Cited Findings
- Meta 공식 Postman 워크스페이스는 Threads API를 콘텐츠 생성·관리·게시용 Graph API 요청 모음으로 설명하며, 시작 절차를 “Threads 사용 사례를 가진 Meta 앱 생성 → 사용자의 데이터 접근 승인 → 액세스 토큰 요청”으로 제시한다. [Meta Threads API 공식 컬렉션](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)
- 공식 컬렉션의 API 호스트는 `https://graph.threads.net`이다. 인증 URL이나 API 버전은 앱 대시보드와 최신 개발자 문서에서 다시 확인해야 한다. [Meta Threads API 공식 컬렉션](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)
- 자기 프로필은 `GET /me?fields=id,username,name,threads_profile_picture_url,threads_biography` 형태로 조회한다. 반환 필드는 요청한 `fields`와 토큰 권한 범위에 좌우된다. [Meta 공식 프로필 요청](https://www.postman.com/meta/threads/request/q9os31a/get-threads-user-s-profile-information)
- 공식 컬렉션에는 `threads_profile_discovery` 권한을 포함한 앱 범위 사용자·공개 프로필 관련 예제가 있고, 프로필 필드 예시는 `id`, `username`, `name`, `is_verified`, 프로필 사진 URL, 소개 등이다. [Meta 공식 앱 범위 프로필 요청](https://www.postman.com/meta/threads/request/k46c8l0/get-app-scoped-user-s-profile-information)
- 게시 기본 흐름은 `POST /{threads-user-id}/threads`로 미디어 컨테이너를 만든 뒤 `POST /{threads-user-id}/threads_publish`에 생성 ID를 전달하는 방식이다. 공식 컬렉션은 `TEXT`, `IMAGE`, `VIDEO`, `CAROUSEL` 게시 폴더를 제공하고, 텍스트 예제는 `/me/threads?...&media_type=TEXT&auto_publish_text=true`로 즉시 게시할 수 있음을 보여 준다. [Meta Threads API 공식 컬렉션](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api?entity=request-34203612-ee0a2365-9d95-4cbe-8087-1cfb04d38c05)
- 컨테이너 상태는 `GET /{container-id}?fields=id,status,error_message`로 확인하며 공식 예제에 `EXPIRED`, `ERROR`, `FINISHED`, `IN_PROGRESS`, `PUBLISHED`가 열거된다. `EXPIRED`는 24시간 안에 게시하지 않은 컨테이너다. [Meta 공식 컨테이너 상태 요청](https://www.postman.com/meta/threads/request/ohuldvi/check-container-s-publishing-status)
- 공개 프로필 게시물 목록 예제는 `GET /profile_posts?username={exact-username}&fields=...`이며, 정확히 일치하는 사용자명이 필요하다. [Meta Threads API 공식 컬렉션](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api?entity=request-34203612-74fb48b1-ad1a-480e-b200-4dcdb8126a2f)

### Inferences
- 교육용 최소 샘플은 “OAuth 연결 → `/me`로 연결 계정 표시 → 텍스트 컨테이너 생성 → 게시 → 게시 ID 저장”의 세로 슬라이스가 적합하다. 이미지·비디오는 외부에서 접근 가능한 미디어 URL 준비와 비동기 상태 확인을 별도 장으로 분리하는 편이 안전하다.
- 앱 토큰과 사용자 토큰을 역할별로 분리해야 한다. 실제 사용자 프로필 조회·게시 요청은 사용자가 승인한 Threads 사용자 액세스 토큰을 사용하고, 앱 토큰을 게시 권한의 대체재로 취급하지 않는다.

### Gaps
- Meta 개발자 문서 본문이 HTTP 429로 열리지 않아 2026-10-23 현재의 정확한 API 버전 표기, 각 미디어 형식 제한, 응답 오류 코드 표 전체는 이 조사에서 재검증하지 못했다. 배포 직전에 [Threads API 개요](https://developers.facebook.com/docs/threads/)와 [변경 로그](https://developers.facebook.com/docs/threads/changelog)를 사람이 직접 확인해야 한다.
- Threads가 지원하는 것은 게시물의 텍스트·이미지·비디오·캐러셀이다. “음악 파일 자체 업로드” 엔드포인트는 확인한 공식 컬렉션에서 찾지 못했으므로 지원한다고 설계하면 안 된다.

## OAuth, 권한, 토큰, 앱 심사와 계정 전제는 무엇인가?

### Takeaway
인증은 OAuth 2.0 Authorization Code 흐름이다. 앱 비밀값은 서버에서만 사용하고, 코드 교환으로 받은 단기 사용자 토큰을 장기 토큰으로 교환해 저장한 뒤 만료 전에 갱신한다. 권한은 기능별 최소 범위로 요청하며, 개발자 역할 계정 밖의 실제 사용자를 받으려면 앱 대시보드의 현재 심사·검증 요구사항을 직접 통과해야 한다.

### Cited Findings
- 공식 컬렉션은 OAuth 2.0 Authorization Code 방식을 요구하며 Auth URL, Access Token URL, Threads App ID, Threads App Secret, Scope을 구성하도록 안내한다. 사용자는 앱의 데이터 접근을 직접 승인해야 한다. [Meta Threads API 공식 컬렉션](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)
- 승인 코드 교환은 `POST https://graph.threads.net/oauth/access_token`에 `client_id`, `client_secret`, `code`, `grant_type=authorization_code`, 최초 요청과 동일한 `redirect_uri`를 전달한다. 응답 예시는 `access_token`과 `user_id`다. [Meta 공식 OAuth 요청 모음](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api?entity=folder-34203612-995a4593-61de-4558-9b26-6c8becae85e4)
- 단기 사용자 토큰은 `GET /access_token?grant_type=th_exchange_token&client_secret=...`로 장기 토큰과 교환한다. 공식 응답 예시의 `expires_in`은 `5184000`초, 즉 60일이다. [Meta 공식 OAuth 요청 모음](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api?entity=request-34203612-b4339073-a559-4e15-9ffe-974d6f0451ec)
- 만료되지 않은 장기 사용자 토큰은 `GET /refresh_access_token?grant_type=th_refresh_token`으로 갱신한다. 공식 컬렉션은 토큰 교환·갱신에는 `threads_basic`만으로 충분하다고 명시한다. [Meta 공식 OAuth 요청 모음](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api?entity=request-34203612-74fb48b1-ad1a-480e-b200-4dcdb8126a2f)
- 앱 토큰은 `GET /oauth/access_token?grant_type=client_credentials&client_id=...&client_secret=...`으로 발급하는 별도 토큰이며 응답 예시는 `TH|...` 형식이다. [Meta 공식 앱 토큰 요청](https://www.postman.com/meta/threads/request/kdhbrk7/get-app-access-token)
- 공식 컬렉션에서 반복 확인되는 권한은 `threads_basic`(기본 접근), `threads_content_publish`(게시), `threads_read_replies`(답글 읽기), `threads_manage_replies`(답글 관리), `threads_manage_insights`(인사이트), `threads_keyword_search`(검색), `threads_manage_mentions`(멘션)이며 최신 예제에는 `threads_delete`, `threads_location_tagging`, `threads_profile_discovery`도 포함된다. [Meta 공식 Threads 요청 컬렉션](https://www.postman.com/meta/threads/request/u22r2j5/control-who-can-reply)
- 액세스 토큰 디버거로 토큰 유형, 부여 권한, 만료 여부를 확인하라는 운영 지침이 공식 컬렉션에 있다. [Meta Threads API 공식 컬렉션](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)
- Meta Platform Terms는 앱이 개발자 문서, 개발자 정책, 관련 법규를 준수해야 하며 위반 시 앱 또는 계정이 정지·종료될 수 있다고 규정한다. [Meta Platform Terms](https://developers.facebook.com/terms)

### Inferences
- 서버 설계에는 `state` 검증, 등록된 리디렉션 URI의 정확 일치, 앱 비밀의 백엔드 전용 보관, 토큰 암호화 저장, 만료 시각 저장, 만료 전 갱신 작업, 연결 해제·권한 철회 처리, 로그의 토큰 마스킹이 필요하다. 이는 공식 OAuth 요청 구조를 안전하게 구현하기 위한 설계 결론이다.
- 기능별 권한 매트릭스를 문서화하고, 초기 MVP는 `threads_basic` + `threads_content_publish`만 요청하는 것이 최소 권한 원칙에 맞다. 답글·인사이트·검색·공개 프로필 발견은 실제 UI 기능이 준비된 뒤 권한과 심사를 추가한다.
- `client_secret`이 필요한 교환 요청을 브라우저에서 직접 실행하면 비밀이 노출되므로 OAuth 콜백과 토큰 교환은 서버 책임이어야 한다.

### Gaps
- 확인한 공식 공개 자료에는 단기 토큰의 정확한 유효시간이 명시되지 않았다. 장기 토큰 60일만 검증되었으므로 단기 토큰을 “1시간”이라고 단정하지 않는다.
- 앱 심사 제출물, 테스트 사용자 초대, 비즈니스 검증 또는 Tech Provider Verification의 정확한 적용 조건은 공식 Threads 문서 본문을 429 때문에 직접 확인하지 못했다. 따라서 “모든 앱에 특정 검증이 필수”라고 단정하지 말고, 앱 대시보드의 `App Review`와 `Required actions`에서 대상 권한별 현재 요건을 확인해야 한다.
- 일반 소비자 계정, 크리에이터/비즈니스 계정 중 어느 유형이 필수인지 공식 컬렉션만으로 확인되지 않았다. 실제 대상 Threads 계정으로 개발 모드 OAuth와 `/me` 호출을 성공시켜 계정 전제를 검증해야 한다.

## 속도 제한, 오류 처리, 운영 요구사항과 API 수명주기는 무엇인가?

### Takeaway
공식 컬렉션은 게시 한도 조회와 컨테이너 상태 확인 수단을 제공하지만 이 조사에서 최신 숫자 한도는 공식 본문으로 재검증되지 않았다. 운영 구현은 숫자를 하드코딩하지 말고 사용량·오류 응답·변경 로그를 기준으로 보수적으로 제어해야 한다.

### Cited Findings
- 게시 할당량은 `GET /me/threads_publishing_limit?fields=...` 요청으로 조회할 수 있다. [Meta 공식 게시 한도 요청](https://www.postman.com/meta/threads/request/34203612-f4590341-9bee-44f5-901b-606078a03c96)
- 컨테이너 상태 API는 `status`와 `error_message`를 반환하도록 요청할 수 있어 비동기 미디어 처리 실패를 진단하는 공식 수단이다. [Meta 공식 컨테이너 상태 요청](https://www.postman.com/meta/threads/request/m47wqlq/check-container-s-publishing-status)
- 공식 Postman 컬렉션은 시간이 지나며 업데이트되지만 최신 기능이 모두 반영되지 않을 수 있으므로 개발자 문서 변경 로그를 최신 기능의 기준으로 삼으라고 경고한다. [Meta Threads API 공식 컬렉션](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)
- Meta는 Threads API가 2024년 6월 출시되어 크리에이터와 비즈니스가 제3자 앱으로 Threads 활동과 게시를 규모 있게 관리하도록 한다고 공식 발표했다. [Meta 공식 제품 발표](https://about.fb.com/news/2024/08/new-threads-features-for-creators-and-businesses/)
- Meta Platform Terms상 앱은 플랫폼 데이터 처리와 관련한 개발자 문서·정책·법률을 계속 준수해야 하며, 정책 위반은 서비스 중단 위험이다. [Meta Platform Terms](https://developers.facebook.com/terms)

### Inferences
- 게시 큐는 요청 전 `threads_publishing_limit`을 확인하고, 한도 임박 시 예약 작업을 지연시켜야 한다. 숫자 상수보다 API가 반환하는 현재 사용량을 진실의 원천으로 삼는다.
- 오류 처리는 HTTP 상태, Meta 오류 객체 전체(민감값 제외), 요청 추적 ID가 있으면 그 값, 대상 사용자·컨테이너 ID, 재시도 횟수를 구조화 로그에 남겨야 한다. 인증 오류는 재승인 경로로, 한도 오류는 지수 백오프·스케줄 연기로, `IN_PROGRESS`는 제한된 폴링으로, `ERROR`·`EXPIRED`는 재생성으로 분기하는 설계가 타당하다.
- API 변경 수명주기는 앱별 API 버전을 한 곳에 고정하고, 변경 로그 정기 확인 → 스테이징 회귀 테스트 → 버전 승격의 절차로 관리해야 한다. 공식 Postman 컬렉션은 실행 예제이지 최신 기능의 완전한 명세가 아니다.

### Gaps
- 2026-10-23 현재 게시·답글·삭제·검색의 정확한 24시간 한도 숫자와 Graph API 전체 호출 예산은 공식 개발자 본문을 열지 못해 검증하지 못했다. 제3자 글의 숫자는 이 문서에 사실로 전재하지 않았다.
- 공식 변경 로그의 개별 날짜·버전별 폐기 일정은 429 때문에 직접 대조하지 못했다. 배포 HOLD 조건으로 [Threads API 변경 로그](https://developers.facebook.com/docs/threads/changelog)와 앱 대시보드 경고를 사람이 확인해야 한다.
- 공식 장애 상태 페이지와 SLA는 이번 조사 범위에서 확인되지 않았다. 운영 전 Meta 개발자 상태/지원 채널의 현재 URL과 알림 구독 방법을 별도로 검증해야 한다.

# 실제 독자 반응 실험과 커뮤니티 게시 API 준비성

## 어떤 지표와 증거를 기록해야 하며, 임의의 통계적 유의성을 선언하지 않으려면 어떻게 해야 하는가?

### Takeaway
실제 반응 검증은 같은 채널·비슷한 시간대·같은 대상에서 기준 문안과 한 요소만 바꾼 문안을 비교하고, 게시 전에 가설·주지표·관찰기간·중단 조건을 고정하는 방식이 가장 방어적이다. 표본이 충분하다고 사전에 근거를 세우지 못한 소규모 운영에서는 승패나 “유의함” 대신 원시 건수, 분모, 비율, 관찰 맥락과 불확실성을 보고해야 한다.

### Cited Findings
- NIST는 실험 설계의 원칙으로 비교, 반복, 무작위화, 통제, 대표성, 블로킹을 제시하며, 같은 조건의 여러 시행이 반응 분포의 변동을 추정하게 한다고 설명한다. — [NIST Technical Note 2340](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=959904)
- GOV.UK의 비교 연구 지침은 A/B 표본을 가능하면 동일 비율로 무작위 배정하고, 표본 크기와 기간은 월간 방문자 수·기대 행동 변화 등 실제 조건에 맞춰 정하며, 결과가 불명확하면 결론을 강요하지 말고 가설이나 변형을 검토해 추가 실험하라고 한다. — [GOV.UK A/B testing guidance](https://www.gov.uk/guidance/ab-testing-comparative-studies)
- Microsoft Research는 한 실험의 가설을 단순하고 측정 가능하게 만들며 복잡한 변경을 각각의 가설로 나누고, 핵심 지표군에 사용자 만족, 가드레일, 기능·참여, 데이터 품질 지표를 포함하라고 제안한다. — [Microsoft Research: pre-experiment patterns](https://www.microsoft.com/en-us/research/?p=680556)
- Microsoft Research의 실험 중 지표 분류는 데이터 품질(오류·데이터 손실), 전체 목표, 기능 진단, 가드레일(이탈·장애 등)을 분리한다. — [Microsoft Research: during-experiment patterns](https://www.microsoft.com/en-us/research/?p=720145)
- Meta Business Suite의 공식 A/B 기능도 먼저 핵심 지표를 하나 선택하며, 후보 지표로 댓글, 공유, 반응, 도달 인원, 링크 클릭을 제시한다. — [Meta Business Help Center](https://z-p4-lookaside.fbsbx.com/business/help/1675344823455042)

### Inferences
- 이 제품에서 실행할 최소 프로토콜은 다음과 같다. (1) 게시 전 `experiment_id`, 채널, 대상 커뮤니티, 가설, 기준 문안 A, 변형 B, **단 하나의 변경 변수**(예: 첫 문장 후크), 주지표, 보조지표, 가드레일, 시작·종료 시각을 고정한다. (2) 플랫폼이 무작위 분할을 지원하면 이를 사용하고, 지원하지 않으면 같은 커뮤니티에서 게시 순서/시간대를 번갈아 배치하되 완전한 무작위 실험이 아니라는 제한을 기록한다. (3) 도중에 잘 나온 버전만 연장하거나 지표를 바꾸지 않는다. 이는 NIST의 비교·반복·무작위화 원칙과 GOV.UK의 사전 기간·표본 결정 지침을 소규모 커뮤니티 운영에 적용한 것이다. — [NIST Technical Note 2340](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=959904); [GOV.UK A/B testing guidance](https://www.gov.uk/guidance/ab-testing-comparative-studies)
- 최소 증거 필드는 `post_id/url`, 문안 버전과 해시, 게시자 승인자, 게시/관찰 시각, 채널·커뮤니티, 노출 또는 도달(분모), CTA 행동 건수(문의·신청·링크 클릭 중 사전 지정 1개), 댓글·공유·저장·반응 건수, 삭제·신고·부정 댓글·운영자 경고, 수집 출처(API/화면 수기), 수집 시각, 누락/오류 여부다. 주지표는 `CTA 행동/노출`처럼 분모가 있는 비율과 원시 건수를 함께 보존하고, 플랫폼이 노출을 주지 않으면 `CTA 행동 수`를 기술 통계로만 보고한다. 이 구성은 Meta가 제공하는 실제 게시 성과 지표와 Microsoft의 목표·가드레일·데이터 품질 분리를 반영한다. — [Meta Business Help Center](https://z-p4-lookaside.fbsbx.com/business/help/1675344823455042); [Microsoft Research: during-experiment patterns](https://www.microsoft.com/en-us/research/?p=720145)
- 정지·안전 규칙은 통계 승패와 별도로 우선한다. 커뮤니티 운영자 경고, 게시물 삭제, 개인정보 노출, 의료·효능 오인, 사용자 신고 또는 플랫폼 약관 위반 신호가 하나라도 확인되면 즉시 게시를 중지하고 `SAFETY_STOP`으로 분류한다. 단순히 반응이 낮은 경우에는 조기 중단으로 좋은 결과만 고르는 대신 사전에 정한 관찰기간을 끝내되, 플랫폼이 안전상 게시를 제한하면 그 상태를 그대로 기록한다. 이는 가드레일 지표를 개선 목표와 별도로 두라는 지침을 적용한 것이다. — [Microsoft Research: during-experiment patterns](https://www.microsoft.com/en-us/research/?p=720145)
- 판정은 `PASS`를 “사전에 정한 조건 아래 B가 A보다 일관되게 유리하고 가드레일 악화가 없으며 원시 증거가 보존됨”으로 제한한다. `HOLD_INSUFFICIENT_EXPOSURE`(노출/CTA가 너무 적어 방향 판단 불가), `HOLD_NOISY`(시간대·대상·형식 등 여러 변수가 함께 변함), `HOLD_DATA_QUALITY`(분모·게시 ID·수집 시각 누락), `NO_LIFT_OBSERVED`(관찰 범위에서 개선 없음), `SAFETY_STOP`을 별도로 둔다. GOV.UK가 불명확한 결과를 불명확하다고 분류하고 다음 실험으로 넘기도록 권하는 점이 이 의미 체계를 뒷받침한다. — [GOV.UK A/B testing guidance](https://www.gov.uk/guidance/ab-testing-comparative-studies)

### Gaps
- 모든 커뮤니티에 통용되는 최소 표본 수나 반응률 기준은 공식 근거에서 확인되지 않았다. 트래픽, 기준 전환율, 탐지하려는 최소 변화, 분산에 따라 달라지므로 제품이 임의의 숫자를 “통계적 유의” 기준으로 내장해서는 안 된다. — [GOV.UK A/B testing guidance](https://www.gov.uk/guidance/ab-testing-comparative-studies)
- 현재 실제 게시 노출·반응 데이터가 제공되지 않았으므로 문안의 실제 독자 효과는 검증되지 않았다. 이 문서는 실행 프로토콜과 증거 계약만 검증한다.

## 희소하거나 잡음이 큰 커뮤니티 데이터는 어떻게 분류해야 하는가?

### Takeaway
0건 반응은 실패와 같지 않고, 노출 분모가 없으면 반응률도 계산할 수 없다. 희소 데이터는 승자 선택이 아니라 추가 증거가 필요한 HOLD로, 여러 조건이 동시에 달라진 데이터는 인과 판단이 불가능한 NOISY로 분류해야 한다.

### Cited Findings
- NIST는 반복 시행이 통제되지 않은 요인 때문에 생기는 반응 변동을 추정하는 수단이라고 설명한다. 반복이 없거나 매우 적으면 변동과 처리 효과를 구분하기 어렵다. — [NIST Technical Note 2340](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=959904)
- GOV.UK는 필요한 실험 기간이 방문자 수와 기대 행동 변화 등에 따라 달라지며, 불명확한 결과는 가설·목표·변형을 검토하고 추가 테스트해야 한다고 명시한다. — [GOV.UK A/B testing guidance](https://www.gov.uk/guidance/ab-testing-comparative-studies)
- Google은 A/B 테스트를 서로 다른 변형에 대한 사용자 행동을 수집·비교하는 과정으로 설명하며, 신뢰할 수 있는 결론에 필요한 기간은 전환율과 트래픽 같은 조건에 따라 달라진다고 설명한다. — [Google Search Central](https://developers.google.com/search/docs/crawling-indexing/website-testing)

### Inferences
- 분류 순서는 `데이터 무결성 → 안전 → 비교 가능성 → 증거량 → 관찰 방향`이어야 한다. 예: 게시 ID나 분모가 없으면 `HOLD_DATA_QUALITY`; 규칙 위반 신호가 있으면 `SAFETY_STOP`; A/B가 다른 채널·요일·대상을 사용하면 `HOLD_NOISY`; 비교 가능한 반복이 부족하면 `HOLD_INSUFFICIENT_EXPOSURE`; 충분성 근거가 사전에 정해졌고 개선이 관찰되지 않으면 `NO_LIFT_OBSERVED`다. 반복과 비교 조건 없이는 처리 효과를 분리하기 어렵다는 NIST 원칙에 따른 분류다. — [NIST Technical Note 2340](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=959904)
- 작은 건수에서는 “B가 2배” 같은 비율만 강조하지 말고 `A: 1/20, B: 2/18`처럼 분자·분모를 함께 제시하고 `방향성 관찰, 결론 보류`라고 쓴다. 노출 0 또는 미수집은 0%가 아니라 `NOT_MEASURED`로 저장한다. 이는 데이터 품질을 별도 지표군으로 관리하라는 Microsoft 지침을 적용한 것이다. — [Microsoft Research: during-experiment patterns](https://www.microsoft.com/en-us/research/?p=720145)
- 각 채널의 결과는 합산 전에 분리 보관한다. 채널별 노출 방식과 이용자 구성이 다르므로, 단순 합산은 한 채널의 대량 노출이 다른 채널의 신호를 덮을 수 있다. 블로킹으로 교란 변수를 통제하라는 NIST 원칙상 채널·커뮤니티·시간대는 분석 블록으로 다루는 편이 타당하다. — [NIST Technical Note 2340](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=959904)

### Gaps
- 플랫폼별 노출·도달·저장·문의 지표의 정의와 제공 범위는 계정 유형과 API 접근 수준에 따라 달라질 수 있다. 실제 계정의 분석 화면 또는 승인된 API 응답 스키마를 확인하기 전에는 채널 간 같은 이름의 지표를 동일 개념으로 합산할 수 없다.
- 자연 게시에서 동일 이용자를 A/B에 무작위 배정할 수 없는 채널은 엄밀한 인과 실험이 아니라 반복 교차 관찰에 가깝다. 제품은 이를 `QUASI_EXPERIMENT`로 표시해야 하며 실제 무작위 실험으로 표현해서는 안 된다.

## Threads·Instagram·X·LinkedIn·Naver 자동 게시에는 무엇이 필요하며 로컬 검사기는 어디까지 확인할 수 있는가?

### Takeaway
공통 최소 조건은 개발자 앱, 사용자 OAuth 동의, 게시 쓰기 권한, 올바른 계정/페이지 역할, 유효 토큰이며 플랫폼에 따라 앱 검토나 제품 접근 승인도 필요하다. 로컬 검사기는 설정의 존재와 형식은 확인할 수 있지만, 비밀값을 보관하지 않은 채 플랫폼 승인·사용자 동의·실제 쓰기 가능성을 증명할 수는 없다.

### Cited Findings
- Threads 공식 Meta Postman 문서는 Threads 사용 사례로 Meta 앱을 만들고 앱 사용자가 데이터 접근을 승인해야 한다고 설명하며, OAuth 2.0 토큰 교환·장기 토큰·갱신 흐름과 `/me/threads_publish` 게시 단계를 제공한다. — [Meta Threads API collection](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)
- Meta의 Instagram 공식 Postman 문서는 Facebook 앱과 사용자 접근 토큰이 필요하고, Facebook Login 방식에서는 Professional Instagram 계정이 Page에 연결돼야 하며 개인 계정은 지원하지 않는다고 설명한다. 게시 관련 권한 예시로 `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement` 등을 제시한다. — [Meta Instagram API collection](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api)
- X 공식 문서 인덱스는 게시 생성 endpoint를 제공하고, X의 API 오류 문서는 API 접근 플랜 등록, 사용자 컨텍스트 인증, 올바른 앱 토큰 권한이 필요하며 403은 endpoint 접근 미승인이나 권한 부족, 429는 rate/post cap 초과일 수 있다고 설명한다. — [X API v2 index](https://docs.x.com/x-api/llms.txt); [X API error guidance](https://developer.x.com/en/support/twitter-api/error-troubleshooting)
- LinkedIn은 OAuth 2.0으로 앱과 사용자를 인증하며 `w_member_social`은 인증된 회원 대신 게시하는 권한이다. 조직 대신 게시하는 `w_organization_social`은 해당 조직에서 관리자·Direct Sponsored Content Poster·Content Admin 역할 중 하나가 필요하다. — [LinkedIn API access](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access); [LinkedIn Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-06)
- LinkedIn Community Management API는 심사 대상 제품이며, 개발 단계 접근 신청에는 승인된 사용 사례, 검증된 회사 이메일·조직·웹사이트/도메인, 연결된 LinkedIn Page의 앱 검증이 요구된다. 표준 단계 심사는 완전한 OAuth 승인 및 실제 게시·성과 표시 흐름을 시연하도록 요구할 수 있다. — [LinkedIn Community Management App Review](https://learn.microsoft.com/en-us/linkedin/marketing/community-management-app-review?view=li-lms-2026-05)
- Naver Cafe 글쓰기 API는 앱 등록, Client ID/Secret, API 권한 설정, Naver Login OAuth 2.0 사용자 접근 토큰이 필요하며, 특정 `clubid`와 `menuid`에 POST한다. 사용자가 해당 권한에 동의하지 않거나 앱의 API 권한이 설정되지 않으면 호출이 실패할 수 있다. — [NAVER Cafe API](https://developers.naver.com/docs/login/cafe-api/cafe-api.md); [NAVER Login guide](https://developers.naver.com/docs/login/devguide/devguide.md)
- Naver의 현재 공식 Open API 목록은 로그인 방식 게시 기능으로 Cafe 가입·글쓰기를 열거하지만 Blog는 검색 API로만 열거한다. 따라서 이 공식 목록만으로 Naver Blog 자동 쓰기 API가 현재 제공된다고 결론낼 수 없다. — [NAVER Open API list](https://developers.naver.com/docs/common/openapiguide/apilist.md)

### Inferences
- 채널별 준비 체크는 다음처럼 분리해야 한다.
  - `Threads`: Meta 앱 ID 존재, Threads 사용 사례/제품 설정 자기확인, HTTPS redirect URI 형식, 요구 scope 선언, 계정 소유자의 OAuth 동의, 토큰 만료·갱신 정책, 게시 전 명시적 사용자 승인. 실제 권한과 게시 가능 여부는 최소 권한의 live profile/token 검사 및 별도 테스트 게시 없이는 `HOLD_PLATFORM_VERIFICATION`이다. — [Meta Threads API collection](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)
  - `Instagram`: Meta 앱, 지원되는 Instagram Professional 계정, 선택한 로그인 방식에 맞는 연결 관계, 게시 scope, 계정 소유자 동의, 필요 시 앱 검토/고급 접근을 확인한다. 개인 계정이면 `UNSUPPORTED_ACCOUNT_TYPE`; 계정 유형과 토큰 권한을 live로 확인하지 못하면 `HOLD_PLATFORM_VERIFICATION`이다. — [Meta Instagram API collection](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api)
  - `X`: 승인된 개발자 앱/프로젝트와 현재 이용 플랜, 사용자 컨텍스트 OAuth, 쓰기 권한, 사용자 동의, rate/post cap 처리 및 재시도·중복 방지 정책이 필요하다. 로컬 설정만으로 현재 플랜의 endpoint 사용 가능성이나 anti-spam 거절 여부를 보장할 수 없다. — [X API v2 index](https://docs.x.com/x-api/llms.txt); [X API error guidance](https://developer.x.com/en/support/twitter-api/error-troubleshooting)
  - `LinkedIn`: 회원 게시에는 OAuth와 `w_member_social`; 조직 게시에는 `w_organization_social`과 허용된 Page 역할이 필요하다. Community Management 제품 접근은 별도 심사/티어 조건이 있으므로 개발자 포털 승인 증거 없이는 자동 게시 준비를 PASS로 두지 않는다. — [LinkedIn API access](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access); [LinkedIn Community Management App Review](https://learn.microsoft.com/en-us/linkedin/marketing/community-management-app-review?view=li-lms-2026-05)
  - `Naver`: Cafe만 자동 게시 후보로 두고 앱 등록·API 권한·OAuth 동의·Cafe 가입 상태·`clubid/menuid`를 확인한다. Naver Blog는 공식 현재 목록에서 쓰기 API를 확인하지 못했으므로 브라우저 수동 인계만 `PASS`, API 자동 게시는 `HOLD_UNSUPPORTED_OR_UNCONFIRMED`로 둔다. — [NAVER Cafe API](https://developers.naver.com/docs/login/cafe-api/cafe-api.md); [NAVER Open API list](https://developers.naver.com/docs/common/openapiguide/apilist.md)
- 비밀을 보관하지 않는 로컬 준비 검사기가 확인할 수 있는 것은 (a) 필요한 환경변수 **이름의 존재 여부와 비어 있지 않음**(값 출력 금지), (b) redirect URI가 HTTPS이고 허용 목록과 정확히 일치하는지, (c) 요구 scope 이름이 구성에 선언됐는지, (d) 공개 privacy policy/terms URL 형식 및 접근 가능 여부, (e) account/page/cafe ID의 형식, (f) 토큰 저장소가 OS secret store 등 외부 비밀 저장소를 가리키는지, (g) 자동 게시 전에 사용자 확인 단계·idempotency key·감사 로그가 설계됐는지다. OAuth 사용자 동의와 플랫폼 심사는 외부 상태이므로 증빙 ID나 live provider 응답 없이는 `SELF_ATTESTED` 또는 `HOLD`다. 각 플랫폼이 사용자 인증·권한·역할 또는 심사를 실제 조건으로 요구한다는 공식 문서에 근거한 경계다. — [Meta Threads API collection](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api); [X API error guidance](https://developer.x.com/en/support/twitter-api/error-troubleshooting); [LinkedIn Community Management App Review](https://learn.microsoft.com/en-us/linkedin/marketing/community-management-app-review?view=li-lms-2026-05); [NAVER Login guide](https://developers.naver.com/docs/login/devguide/devguide.md)
- 준비 상태 의미는 `LOCAL_READY`(형식·필수 구성 PASS), `CONSENT_REQUIRED`, `REVIEW_REQUIRED`, `TOKEN_NOT_TESTED`, `LIVE_READ_PASS`(최소 권한 읽기 호출 성공), `LIVE_WRITE_PASS`(계정 소유자가 승인한 비공개/삭제 가능한 시험 게시와 정리까지 성공), `HOLD_UNSUPPORTED_OR_UNCONFIRMED`로 나눠야 한다. `LOCAL_READY`는 자동 게시 가능을 뜻하지 않으며, 사용자 승인 없는 실게시를 readiness test로 실행해서는 안 된다.

### Gaps
- Meta 개발자 문서 원문은 조사 시점에 자동 수집 요청에 429를 반환하여, Meta가 게시한 공식 Postman 컬렉션을 1차 대체 자료로 사용했다. 선택할 Instagram 로그인 방식에 따라 scope 이름과 연결 요건이 달라질 수 있으므로 구현 직전 App Dashboard의 현재 제품 문서로 재확인해야 한다.
- X의 가격·플랜·쓰기 한도는 변동 가능하며 이 조사에서는 특정 플랜의 수치나 비용을 확정하지 않았다. 실제 개발자 계정의 현재 포털과 endpoint 응답으로 확인해야 한다.
- LinkedIn과 Meta의 심사 승인 여부, 각 계정의 관리자 역할, OAuth 동의, Naver Cafe 가입·게시판 쓰기 권한은 로컬 파일만으로 검증할 수 없다.
- 실제 플랫폼에 게시하거나 계정 권한을 변경하는 검증은 수행하지 않았다. 계정 소유자의 명시적 동의, 테스트 대상/삭제 계획, 플랫폼별 자격 증명이 제공된 뒤 별도 live 검증으로 남는다.

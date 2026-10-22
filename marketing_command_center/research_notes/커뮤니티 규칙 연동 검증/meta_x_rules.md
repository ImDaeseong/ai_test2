# Meta Threads·Instagram 및 X 공식 규칙 조사

검토일: 2026-10-22. 아래 근거는 Meta·Instagram·X가 직접 게시한 정책, 도움말, 개발자 문서와 Meta 공식 Postman 워크스페이스만 사용했다. 정책 적용 여부는 게시물의 문맥·계정 행태·지역 법률에 따라 달라질 수 있다.

## 오프라인 검사기가 경고할 홍보·스팸·기만 규칙은 무엇인가

### Takeaway
검사기는 반복·대량·무관한 홍보, 동의 없는 상업적 연락, 조작된 참여, 허위·과장 주장, 기만 링크, 사칭, 무권리 콘텐츠, 보상 관계 미표시를 경고할 수 있다. 그러나 단어 하나로 위반을 확정하지 말고 `경고 + 게시자 확인`으로 표시해야 한다.

### Cited Findings
- Instagram 지침은 인위적인 좋아요·팔로워·공유 수집, 반복 댓글·콘텐츠, 상대 동의 없는 반복적 상업 연락, 참여 대가로 금전 또는 금전성 경품 제공, 가짜·오도성 리뷰 거래를 금지한다. 또한 자신이 만들었거나 공유 권리가 있는 사진·영상만 게시하고, 타인을 사칭하거나 오도 목적으로 계정을 만들지 말라고 요구한다. 이 지침은 2024년 11월부터 Meta Community Standards로 통합되어 Instagram·Threads·Facebook·Messenger에 공통 적용된다고 안내한다. — [Instagram Community Guidelines (Meta/Instagram Help Center)](https://www.facebook.com/help/477434105621119?locale=en_GB)
- Meta Safety Center는 Community Standards가 Facebook, Instagram, Threads, Messenger에 공통 기반을 제공한다고 명시한다. 따라서 Threads 전용 문구 검사도 Meta 공통 기준과 Instagram의 구체적 스팸 지침을 함께 참조하는 편이 안전하다. — [Meta Safety Policies](https://www.meta.com/safety/topics/safety-basics/policies/)
- X Authenticity Policy는 대량·중복·무관·원치 않는 게시, 대량 멘션/답글/DM, 관심을 끌기 위한 무관한 인기 해시태그, 설명 없는 링크 반복, 무관한 답글 홍보, 동일·유사 게시 반복, 기존 참여도를 악용하는 기만 편집, 목적지가 바뀐 링크를 금지한다. 팔로우/참여 교환·구매와 자동화로 트래픽을 인위적으로 올리는 행위도 금지한다. — [X Authenticity Policy](https://help.x.com/en/rules-and-policies/authenticity)
- X는 사기성 할인, 피싱, 돈·재산·개인정보를 얻기 위한 사회공학 등 사기 수법과 악성·기만 링크를 금지한다. — [X Authenticity Policy](https://help.x.com/en/rules-and-policies/authenticity)
- X의 유료 광고 정책은 과장·선정적·부정확한 클릭베이트, 오도성 제품·서비스 주장, 실제로 제공되지 않는 혜택, 가격·지급 조건·비용 같은 핵심 정보 누락을 기만적 홍보로 본다. 이 페이지는 유료 광고/수익화에 직접 적용되므로 일반 유기 게시물에는 `광고 집행 시 필수 검토` 규칙으로 구분해야 한다. — [X Deceptive & Fraudulent Content](https://help.x.com/en/business-and-advertising/deceptive-and-fraudulent-content)
- X는 제3자 브랜드가 크리에이터에게 보상 또는 인센티브를 제공한 유기 게시물에 상업적 관계를 나타내는 `#ad`를 포함하도록 요구한다. API에도 `paid_partnership` 필드가 있다. — [X Account Behavior Rules](https://help.x.com/en/rules-and-policies/x-rules-and-best-practices); [X Create Posts API](https://docs.x.com/x-api/posts/create-post)
- X API는 AI 생성 미디어 공개용 `made_with_ai` 필드를 제공한다. X Rules는 해를 일으킬 가능성이 있는 기만적 합성·조작 미디어를 금지한다. 텍스트가 AI로 보조 작성됐다는 이유만으로 이 필드를 켜야 한다고 문서는 말하지 않으므로 검사기는 `AI 생성 미디어 포함 여부`를 별도 질문해야 한다. — [X Create Posts API](https://docs.x.com/x-api/posts/create-post); [The X Rules](https://help.x.com/rules-and-policies/twitter-rules.html)
- X의 자동화 규칙은 자동 게시/DM의 스팸, 트렌드 자동 편승, 한 계정 또는 여러 계정의 중복·유사 게시, 오도성 리디렉션 링크, 민감 미디어 미표시, 무단 개인정보 게시를 금지한다. AI 답글 봇은 X의 사전 서면 명시 승인을 요구한다. — [X Automation Rules](https://help.x.com/en/rules-and-policies/x-automation)
- X 프로모션/콘테스트 지침은 다중 계정 참가를 막고, 동일 게시 반복을 유도하지 않으며, 관련 있는 해시태그만 쓰고, 적용 법률과 규정을 운영자가 확인하도록 요구한다. — [X Promotions Guidelines](https://help.x.com/en/rules-and-policies/x-contest-rules)

### Inferences
- 구현 가능한 정적 경고: `동일·유사 문안 반복`, `과도하거나 무관한 해시태그`, `링크만 있는 게시`, `좋아요/팔로우/리뷰 대가 지급`, `동의 없는 DM·멘션 유도`, `지나친 긴급성·보장·최고/유일 표현`, `가격·조건 누락`, `사칭 암시`, `개인정보 포함`, `#ad/paid_partnership 누락 가능성`, `AI 생성 미디어 공개 확인`, `콘테스트 법적 조건 확인`.
- 문안 생성기는 같은 캠페인을 여러 채널에 그대로 복제하지 말고 각 채널에 맞춰 의미 있게 재작성해야 한다. 특히 X 자동 게시 전에는 최근 게시물과의 유사도·빈도·링크 목적지를 확인하는 회귀 가드가 필요하다.
- `마사지 연습 상대 모집` 같은 게시물은 치료 효과·통증 개선·전문 자격을 입증 없이 단정하면 기만 가능성이 커진다. 검사기는 의료·자격·효과 표현을 사람 검수로 승격하고, 대가·무료 범위·장소·개인정보 처리·연락 방식이 빠졌는지 경고하는 것이 적절하다.

### Gaps
- Meta의 공통 Community Standards 세부 Fraud/Spam 페이지는 조사 시점에 자동 열람이 제한되었다. 따라서 위 Meta 세부 항목은 접근 가능한 Instagram 공식 지침에 근거하며, 배포 직전 Meta Transparency Center 원문을 사람이 다시 열어 최신 문구와 지역별 예외를 확인해야 한다.
- 공식 정책은 `과도한`, `반복적`, `원치 않는`의 보편적 숫자 임계값을 제공하지 않는다. 검사기가 임의의 게시 횟수나 해시태그 개수를 플랫폼의 공식 한도로 표시하면 안 된다.

## 무엇을 자동 판정할 수 없으며 사람 HOLD로 남겨야 하는가

### Takeaway
문맥, 사실성, 권리, 동의, 보상 관계, 지역 법률, 커뮤니티별 자체 규칙은 정적 분석만으로 판정할 수 없다. 자동 검사는 위험 신호를 보여주되 최종 `게시 가능` 판정은 계정 소유자 또는 지정 검수자가 내려야 한다.

### Cited Findings
- Instagram은 상업적 연락이 반복인지, 상대 동의가 있었는지, 이미지·영상에 대한 공유 권리가 있는지를 요구한다. 이 사실들은 게시문 본문만으로 확인할 수 없다. — [Instagram Community Guidelines](https://www.facebook.com/help/477434105621119?locale=en_GB)
- X는 콘텐츠가 대량·중복·무관·원치 않는지, 해시태그가 대화를 조작할 의도인지, 미디어 문맥이 기만적인지 등을 행태와 문맥에 따라 판단한다. — [X Authenticity Policy](https://help.x.com/en/rules-and-policies/authenticity)
- X는 유료 파트너십 표시를 보상 또는 인센티브가 있는 제3자 브랜드 관계에 연결한다. 보상 관계는 문안만 보고 확정할 수 없다. — [X Account Behavior Rules](https://help.x.com/en/rules-and-policies/x-rules-and-best-practices)
- X 콘테스트 지침은 적용 법률 준수 책임을 운영자에게 두며 법률 질문은 변호사에게 상담하도록 안내한다. — [X Promotions Guidelines](https://help.x.com/en/rules-and-policies/x-contest-rules)
- Instagram/Meta 정책은 테러, 조직범죄, 증오, 성적 서비스, 총기·주류·담배·약물 등 규제·고위험 범주를 다루며, 실제 허용 여부는 게시 내용·거래 주체·지역·맥락에 좌우된다. — [Instagram Community Guidelines](https://www.facebook.com/help/477434105621119?locale=en_GB)

### Inferences
- 사람 HOLD 체크리스트에는 최소한 `주장 증빙`, `전문 자격/의료 표현`, `사진·후기·상표 사용권`, `등장 인물 동의`, `대가/협찬/무료 조건`, `개인정보와 연락 동의`, `해당 커뮤니티 관리자 규칙`, `지역 광고·경품·업종 법률`, `최근 게시물과의 반복성`, `링크 최종 목적지`, `AI 생성 미디어 표시`가 있어야 한다.
- 각 커뮤니티(예: 특정 지역 카페/그룹)의 가입 조건, 홍보 허용 요일, 말머리, 지역 제한, 연락처 노출 규칙은 플랫폼 전체 정책과 별도다. 게시 직전에 사람이 실제 커뮤니티 공지와 운영자 규칙을 확인해야 한다.
- 반응률은 정책 준수 여부가 아니라 실제 대상·채널·시점의 성과 지표다. 자동화 전 최소한 게시 ID, 채널, 버전, 노출/조회, 클릭 또는 문의, 유효 문의, 신고·삭제 여부를 기록하고 여러 문안 사이의 성과를 비교해야 하며, 가짜 참여를 만들거나 구매해서는 안 된다.

### Gaps
- 공식 문서는 개별 지역 커뮤니티의 자체 규칙이나 한국의 업종별 광고·의료·개인정보 법률 준수를 대신하지 않는다.
- 실제 반응률은 게시 전 검증할 수 없다. 실계정의 소규모 게시와 사전 정의한 측정 기간·성공 지표가 필요하다.

## 게시 API에는 어떤 계정·앱 권한과 검토가 필요한가

### Takeaway
세 플랫폼 모두 자동 게시에는 계정 소유자의 명시적 OAuth 권한과 개발자 앱 설정이 필요하다. 현 단계에서는 `복사 후 공식 앱에서 사람이 게시`가 검증 가능한 안전 경계이며, API 자동 게시는 앱 등록·권한 승인·토큰·실계정 샌드박스 검증이 끝난 뒤 별도 기능으로 열어야 한다.

### Cited Findings
- Threads 공식 API 시작 절차는 Threads 사용 사례가 있는 Meta 앱 생성, 사용자의 데이터 접근 승인(OAuth 2.0), 올바른 권한을 가진 토큰 발급을 요구한다. 게시에는 최소 `threads_basic` 및 `threads_content_publish`가 관련되며, 답글·인사이트에는 `threads_read_replies`, `threads_manage_replies`, `threads_manage_insights` 등의 별도 권한이 쓰인다. — [Meta official Threads API Postman documentation](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)
- Threads 공식 컬렉션은 텍스트·이미지·영상·캐러셀 게시를 위한 API이며, 권한 부여 후 단기 토큰을 장기 토큰으로 교환하고 만료 전 갱신하는 흐름을 제공한다. — [Meta official Threads API Postman documentation](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)
- Instagram API with Facebook Login은 Facebook Page에 연결된 Instagram Professional 계정(Business 또는 Creator)을 대상으로 하며 일반 소비자 계정은 접근할 수 없다. 게시 관련 권한 예시는 `pages_show_list`, `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`이고, Stories 게시 지원은 Business 계정으로 제한된다고 공식 컬렉션이 설명한다. — [Meta official Instagram API Postman documentation](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api)
- X의 게시 생성 엔드포인트는 `POST /2/tweets`이며 OAuth 2.0 인가 서버에서 받은 액세스 토큰을 요구한다. 현재 API는 `made_with_ai`와 `paid_partnership` 공개 필드를 제공한다. — [X Create Posts API](https://docs.x.com/x-api/posts/create-post)
- X 개발자 문서는 쓰기 작업에 승인된 개발자 계정·Project/App과 사용자 액세스 토큰(OAuth 1.0a 또는 OAuth 2.0 PKCE)이 필요하다는 공통 전제와, 앱이 쓰기 권한이 없으면 403/오류 261이 발생할 수 있음을 설명한다. — [X Developer Platform Quickstart](https://docs.x.com/make-your-first-request); [X API Error Support](https://developer.x.com/en/support/twitter-api/error-troubleshooting)
- X 자동화 정책은 개발자 정책을 따르지 않는 자동화와 스팸 자동 게시를 금지하고, 위반 시 연결 계정과 API 접근이 제한·정지·종료될 수 있다고 밝힌다. — [X Automation Rules](https://help.x.com/en/rules-and-policies/x-automation)

### Inferences
- 제품에서 `연결됨`은 환경변수 존재가 아니라 OAuth 사용자, 계정 ID, 승인 범위, 토큰 만료, 읽기 프로필 확인까지 성공한 상태여야 한다. 비밀 토큰 값은 UI·로그·검증 보고서에 노출하지 않아야 한다.
- 자동 게시 버튼의 전제 조건은 `계정 소유자 동의`, `최소 권한`, `게시 직전 최종 미리보기`, `명시적 확인`, `중복/빈도 가드`, `정확한 실패 분류`, `게시 ID와 감사 로그`, `토큰 철회·만료 처리`다. Threads·Instagram·X 각각 별도 어댑터와 권한 상태를 보여줘야 한다.
- Threads와 Instagram의 실제 앱 검토/Advanced Access 필요 여부는 앱이 자체 소유 계정만 쓰는지, 제3자 사용자를 받는지, 선택한 로그인 방식과 권한에 따라 달라질 수 있다. 공식 앱 대시보드가 요구하는 검토 항목과 화면 녹화·개인정보처리방침을 실제 앱 구성에서 확인하기 전에는 `검토 완료`라고 표시하지 않아야 한다.
- 현 제품의 수동 인계는 사용자가 본문을 검토하고 공식 플랫폼에서 최종 게시하므로 플랫폼 토큰과 게시 권한이 없는 상태에서도 정직하게 `수동 게시 가능 / API 자동 게시 미설정`으로 표시할 수 있다.

### Gaps
- Meta 개발자 사이트는 조사 시점에 자동 요청을 429로 차단했다. 공식 Postman 컬렉션으로 현재 권한 이름과 계정 제한을 확인했지만, App Review·Advanced Access의 정확한 적용은 앱 대시보드에서 해당 앱·사용 사례 기준으로 사람이 재확인해야 한다.
- 실제 Meta/X 앱 ID, 승인 상태, OAuth 리디렉션 URI, 계정 소유권, 토큰 범위가 제공되지 않았으므로 실게시 API 호출은 검증하지 않았다.

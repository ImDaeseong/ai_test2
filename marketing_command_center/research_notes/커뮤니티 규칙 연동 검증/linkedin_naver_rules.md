# LinkedIn·네이버 홍보 게시 규칙과 연동 경계

> 확인일: 2026-10-22. LinkedIn/Microsoft, NAVER, 공정거래위원회의 공식 1차 자료만 사용했다.

## 어떤 규칙을 경고 또는 게시 전 체크박스로 변환할 수 있는가?

### Takeaway
거짓·과장 주장, 무차별·반복 홍보, 인위적 반응 유도, 권리·개인정보 침해, 대가성 추천의 관계 미공개는 공통 경고로 구현할 수 있다. 다만 주장의 진실성, 이미지·이름 사용권, 경제적 이해관계 표시의 충분성은 사람이 최종 확인해야 한다.

### Cited Findings
- LinkedIn은 무차별·무관한·원치 않는·무승인 홍보와 과도하게 반복되는 콘텐츠를 금지하며, 모르는 사람에게 초대 기능으로 홍보 메시지를 보내지 말라고 한다. 원본성·전문성·관련성·흥미를 갖춘 콘텐츠를 권한다. — [LinkedIn Professional Community Policies](https://www.linkedin.com/legal/professional-community-policies)
- LinkedIn은 이모지/반응 투표, 체인 메시지식 좋아요·공유 요청, 반복·무관한 댓글과 메시지, 검색엔진 조작 목적의 오도성 기사를 스팸 예시로 든다. — [LinkedIn Spam Help](https://www.linkedin.com/help/linkedin/answer/a1338787)
- LinkedIn은 사업·자격·경력·소속·성과에 관한 오도성 정보와 거짓 프로필을 금지한다. 금전이나 무료 제품·서비스 등 이익을 받고 하는 추천은 그 이익을 명확하고 눈에 띄게 공개해야 한다. — [LinkedIn Professional Community Policies](https://www.linkedin.com/legal/professional-community-policies)
- 네이버는 상품·서비스를 과도하게 홍보·판매·알선하거나, 홍보 목적으로 URL을 반복 등록하거나, 자신을 추천인으로 적어 가입을 부탁하는 행위를 대표적인 제한 유형으로 제시한다. — [NAVER 홍보성 게시물](https://help.naver.com/service/19212/contents/7997?lang=ko&osType=COMMONOS)
- 네이버는 무허가 자동화 게시, 서비스 취지와 무관한 콘텐츠, 홍보·광고·판매 목적의 동일·유사 게시물을 지속 반복하여 불편을 주는 행위를 제한한다. — [NAVER 게시물 운영정책](https://policy.naver.com/policy/service_group.html)
- 네이버는 타인의 비공개 개인정보·사생활 노출과 명예·초상권·저작권 침해를 제한한다. 카페 상품 등록에서는 허위정보·금칙어·개인정보·부적절한 사진이 있으면 등록 거부나 이용 제한이 가능하다고 안내한다. — [NAVER 게시물 운영정책](https://policy.naver.com/policy/service_group.html); [NAVER 카페 안전거래 유의사항](https://help.naver.com/service/5622/contents/24561?lang=ko&osType=COMMONOS)
- 공정거래위원회는 제3자의 독립적 의견처럼 보이는 추천·보증에서 사업자로부터 받은 대가를 숨기면 기만적 광고가 될 수 있어 경제적 이해관계를 공개해야 한다고 안내한다. 광고주가 운영하는 계정임을 소비자가 쉽게 아는 경우와, 임직원 관계 등을 소비자가 알 수 없는 경우를 구분한다. — [공정거래위원회 경제적 이해관계 표시 안내](https://www.ftc.go.kr/DATA/download/www/cts304_file.pdf)

### Inferences
- 자동 경고 후보: 반복 URL·유사 문구, 좋아요·공유·추천을 요구하는 인위적 반응 유도, 추천인 코드, 검증되지 않은 보장·치료·자격·성과 단정, 타인 연락처·신상정보, 대가성 추천 의심 표현, 허가 없는 이미지·후기.
- 게시 전 필수 확인: '직접 입증할 수 있는 주장만 있다', '개인정보·사진·후기 사용 권한이 있다', '대가·협찬·임직원 관계를 초반에 눈에 띄게 표시했다', '무차별 반복 게시가 아니다'.
- 오프라인 모집문은 활동 성격, 유료/무료, 전문 서비스·진료 여부, 장소·시간 협의 방식, 신체 접촉 범위와 언제든 중단 가능함, 민감정보를 공개 댓글로 받지 않는다는 점을 사람이 확인하도록 하는 것이 플랫폼의 정확성·개인정보·원치 않는 접근 금지 원칙과 부합한다.

### Gaps
- 주장·후기의 진실성, 권리 동의의 유효성, 이해관계 표시가 실제 화면에서 충분히 눈에 띄는지는 자동 PASS로 바꿀 수 없다.
- 오프라인 만남의 세부 안전 절차는 검토한 플랫폼 규칙에 단일 표준으로 제시되지 않았다. 신체 접촉·미성년자·서비스 자격에 관한 별도 법률·안전 검토가 필요하다.

## 무엇이 커뮤니티·그룹별 규칙이므로 전역 규칙처럼 단정할 수 없는가?

### Takeaway
네이버 카페·블로그는 홍보 기준을 다른 네이버 서비스보다 완화하지만 세부 제한은 서비스·카페·게시판별로 다르다. 제목·말머리·홍보 허용 여부·글쓰기 등급·외부 링크·모집 허용은 게시 직전에 사람이 해당 공지와 게시판 설정을 확인해야 한다.

### Cited Findings
- 네이버는 카페·블로그에 서비스 특성을 고려해 홍보성 기준을 완화하며, 제한 게시물의 상세 유형은 서비스 특성에 따라 다를 수 있다고 명시한다. — [NAVER 홍보성 게시물](https://help.naver.com/service/19212/contents/7997?lang=ko&osType=COMMONOS)
- 네이버 카페의 읽기·댓글·글쓰기 권한은 운영진이 게시판별로 설정하며, 전체 공개와 멤버 공개 범위도 다르다. — [NAVER 카페 게시판 권한 설정](https://help.naver.com/service/5622/contents/15704?lang=ko&osType=PC)
- 네이버 카페 API는 상품 게시판 글쓰기를 지원하지 않고, 접근·등급·메뉴 제한 또는 운영진의 금칙어·스팸 자동 차단에 따라 403 오류를 반환할 수 있다. — [NAVER 카페 가입·글쓰기 API](https://developers.naver.com/docs/login/cafe-api/cafe-api.md)
- 네이버 인플루언서 키워드 챌린지는 키워드와 무관한 내용, 채널만 바꿔 복사한 중복 콘텐츠, 링크 위주 콘텐츠 등을 부적합으로 분류한다. — [NAVER 인플루언서 운영원칙](https://help.naver.com/service/22665/contents/14128?lang=ko)

### Inferences
- 카페별 필수 사람 확인 항목: 가입·글쓰기 등급, 홍보·모집 허용 게시판, 말머리·제목 형식, 외부 링크·연락처 규칙, 게시 횟수, 교차 게시, 지역·연령·자격 제한. 공지 URL과 확인일을 저장해야 한다.
- 이 확인이 없으면 상태를 'HOLD: community rules unverified'로 두고, API 권한이 있어도 규칙 준수 PASS로 간주하지 않는다.
- 채널만 바꿔 같은 문안을 복제하지 않고 각 공동체의 독자·주제·게시판 목적에 맞게 수정했는지 확인한다.

### Gaps
- 개별 카페의 공지·금칙어·승인 절차는 대상 카페와 게시판을 지정하지 않으면 알 수 없다.
- LinkedIn 개별 그룹 규칙과 가입 상태도 인증 계정·대상 그룹 지정 없이는 전역적으로 확인할 수 없다.

## 게시 연동에 어떤 API·계정 권한·파트너 승인이 필요한가?

### Takeaway
LinkedIn 개인 게시에는 OAuth 2.0 회원 동의와 'w_member_social'이 필요하다. 조직 게시는 페이지 역할, 'w_organization_social', Community Management API 접근을 별도 확인해야 한다. 네이버 카페는 앱 등록·네이버 로그인 OAuth·API 권한·해당 게시판 권한으로 공식 게시가 가능하지만, 네이버 블로그 외부 글쓰기 API는 종료됐다.

### Cited Findings
- LinkedIn API는 OAuth 2.0을 사용하며, 회원 자원에 접근해 대신 요청하는 앱은 3-legged member authorization으로 회원 승인을 받아야 한다. — [LinkedIn OAuth 2.0 Overview](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication)
- 'w_member_social'은 인증 회원을 대신해 게시·댓글·좋아요를 수행하는 권한이며 Share on LinkedIn 제품의 Open Permission이다. 다른 대부분의 LinkedIn 권한·파트너 프로그램은 명시적 승인을 요구한다. — [LinkedIn API Access](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access)
- 조직 게시용 'w_organization_social'은 인증 회원이 해당 페이지의 ADMINISTRATOR, DIRECT_SPONSORED_CONTENT_POSTER, CONTENT_ADMIN 중 한 역할을 가져야 한다. 현행 Posts API는 'POST https://api.linkedin.com/rest/posts'와 버전 헤더를 요구하며 기존 ugcPosts API를 대체한다. — [LinkedIn Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api)
- 네이버 카페 글쓰기 API는 애플리케이션 등록, Client ID/Secret, API 권한 설정, 네이버 로그인 OAuth 2.0 접근 토큰을 요구하며 'POST /v1/cafe/{clubid}/menu/{menuid}/articles'로 글을 등록한다. 권한이 앱에 없으면 403이 발생한다. — [NAVER 카페 가입·글쓰기 API](https://developers.naver.com/docs/login/cafe-api/cafe-api.md)
- 네이버는 외부 서비스의 블로그 글쓰기 Open API를 2020-05-06 종료했다. 반복적·기계적으로 유사한 글을 대량 발행하는 정책 위반을 종료 사유로 밝혔다. — [NAVER 블로그 Open API 종료](https://developers.naver.com/notice/article/7527)
- 네이버 로그인은 기본 식별자 외 프로필 정보를 요청하면 활용 사례를 사전 검수하며, 불필요한 정보 요청이나 확인할 수 없는 서비스 자료는 반려 사유가 된다. — [NAVER 로그인 사전 검수](https://developers.naver.com/docs/login/verify/verify.md)

### Inferences
- 상태를 'MANUAL', 'CONFIGURED_NOT_VERIFIED', 'AUTHORIZED', 'READY_TO_POST', 'HOLD_RULES', 'POSTED', 'FAILED'로 분리한다. 토큰 보유를 규칙 검증이나 최종 게시 동의와 혼동하지 않는다.
- LinkedIn 개인 게시와 조직 게시를 분리한다. 조직 게시에는 페이지 역할·조직 URN·'w_organization_social'·Community Management API 접근 확인을 별도 HOLD로 둔다.
- 네이버 카페는 공식 API만 사용하고, 사용자 미리보기·규칙 확인·명시적 게시 승인을 요구한다. AP002–AP005 같은 권한·스팸 오류를 본문이 포함되지 않은 안전한 상태로 기록한다.
- 네이버 블로그는 비공식 브라우저 자동화로 우회하지 않고 '본문 복사 + 공식 작성 화면 열기 + 사용자 직접 게시'를 유지한다.
- 게시만 필요하면 프로필·이메일 등 불필요한 개인정보 권한을 요청하지 않는다.

### Gaps
- 실제 앱, Redirect URI, 계정 소유자, 대상 페이지·카페, 관리자/멤버 역할, 심사 결과가 제공되지 않아 실제 생성 게시 API 호출은 검증할 수 없다.
- LinkedIn 조직용 Community Management API의 실제 승인 범위는 앱과 사용 사례를 제출한 뒤 Developer Portal의 상태로 확인해야 한다.

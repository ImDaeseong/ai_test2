# LinkedIn 설정

Posts API는 텍스트, 이미지, 영상, 문서, 기사와 여러 특수 게시 유형을 지원합니다. 이미지·영상·문서는 먼저 각 자산 API로 업로드해 URN을 받은 뒤 Posts API에 연결해야 합니다. 독립 오디오 게시 유형은 확인되지 않았습니다.

```powershell
$env:LINKEDIN_ACCESS_TOKEN = "사용자 OAuth 토큰"
$env:LINKEDIN_AUTHOR_URN = "urn:li:organization:123456"
$env:LINKEDIN_VERSION = "202610"
python cli.py linkedin --text "회사 소식"
python cli.py linkedin --text "자료 설명" --media-type DOCUMENT --media-id "urn:li:document:..."
```

현재 코드는 텍스트 게시와 **이미 업로드된** 이미지·영상·문서 URN 연결을 지원합니다. 자산 바이너리 업로드는 HOLD입니다. 조직 게시에는 조직 역할과 `w_organization_social`, 개인 게시에는 승인된 `w_member_social`이 필요합니다.

공식 근거: [Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-10), [버전 변경](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/recent-changes?view=li-lms-2026-10).

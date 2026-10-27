# Reddit 설정

Reddit은 텍스트, 링크, 이미지, 영상/GIF 게시 유형을 지원합니다. 게시 가능 유형과 규칙은 subreddit별로 다르고, 앱/API 접근 승인과 사용자 OAuth가 필요할 수 있습니다. 독립 오디오·일반 파일 게시 유형은 확인되지 않았습니다.

```powershell
$env:REDDIT_ACCESS_TOKEN = "사용자 OAuth 토큰"
$env:REDDIT_SUBREDDIT = "community_name"
python cli.py reddit --title "제목" --text "본문"
python cli.py reddit --title "링크" --text "설명" --media-type LINK --media-url "https://example.com"
```

현재 코드는 텍스트와 링크만 실행합니다. 이미지·영상은 Reddit 미디어 업로드/Devvit 실행 문맥이 별도로 필요하므로 HOLD입니다. 자동 반복 게시 전 subreddit 규칙과 스팸 정책을 사람이 검토해야 합니다.

공식 근거: [SubmitMediaOptions](https://developers.reddit.com/docs/api/redditapi/models/type-aliases/SubmitMediaOptions), [RedditClient submitPost](https://developers.reddit.com/docs/api/public-api/classes/RedditClient).

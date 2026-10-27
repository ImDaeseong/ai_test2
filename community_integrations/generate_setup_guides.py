"""Generate per-community HTML guides from the reviewed adapter configuration."""

from __future__ import annotations

from html import escape
from pathlib import Path


OUTPUT = Path(__file__).parent / "docs" / "community-setup"

# id, name, current scope, site setup, environment values, dry-run, HOLD, official links
PLATFORMS = [
    ("threads", "Threads", "텍스트·공개 HTTPS 이미지·영상", ["Meta for Developers에서 Threads 사용 사례 앱을 만든다.", "OAuth Redirect URI를 등록한다.", "threads_basic, threads_content_publish 권한을 요청하고 사용자 동의를 완료한다."], [("THREADS_USER_ID", "Threads 사용자 ID", 0), ("THREADS_ACCESS_TOKEN", "사용자 액세스 토큰", 1)], 'python cli.py threads --text "설정 테스트"', "미디어는 공개 HTTPS URL이 필요하며 실제 게시 전 앱 권한과 대상 계정을 확인한다.", [("Threads API", "https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api")]),
    ("instagram", "Instagram", "Professional 계정 미디어 게시", ["계정을 Business 또는 Creator Professional 계정으로 전환한다.", "Meta 앱에서 Instagram 로그인/그래프 연동을 설정한다.", "instagram_content_publish 또는 동등 권한을 승인받는다."], [("INSTAGRAM_USER_ID", "Professional 계정 사용자 ID", 0), ("INSTAGRAM_ACCESS_TOKEN", "사용자 액세스 토큰", 1)], 'python cli.py instagram --text "이미지 설명" --media-type IMAGE --media-url "https://example.com/a.jpg"', "개인 계정은 대상이 아니며 Reels·Stories·큰 영상은 처리 상태 확인이 필요하다.", [("Instagram API", "https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api")]),
    ("telegram", "Telegram", "Bot 텍스트·원격 미디어", ["@BotFather에게 /newbot을 보내 Bot을 만든다.", "Bot을 대상 그룹 또는 채널에 추가한다.", "채널 게시라면 Bot에 게시 관리자 권한을 준다."], [("TELEGRAM_BOT_TOKEN", "BotFather가 발급한 Bot 토큰", 1), ("TELEGRAM_CHAT_ID", "@채널사용자명 또는 chat ID", 0)], 'python cli.py telegram --text "설정 테스트"', "로컬 파일 multipart 업로드는 아직 구현하지 않았다.", [("Bot API", "https://core.telegram.org/bots/api")]),
    ("tiktok", "TikTok", "Content Posting API 사진·영상", ["TikTok for Developers에서 앱과 Content Posting API를 등록한다.", "Direct Post와 video.publish 권한을 승인받는다.", "PULL_FROM_URL 미디어 도메인을 검증한다."], [("TIKTOK_ACCESS_TOKEN", "사용자 액세스 토큰", 1)], 'python cli.py tiktok --text "영상 설명" --media-type VIDEO --media-url "https://verified.example.com/a.mp4" --privacy-level SELF_ONLY', "앱 감사와 공유 지침 적합성 확인 전 공개 게시를 진행하지 않는다.", [("Direct Post", "https://developers.tiktok.com/docs/en/content-posting-api-get-started")]),
    ("x", "X", "텍스트 Post 생성", ["Developer Console에서 Project와 App을 만든다.", "사용자 OAuth와 쓰기 권한을 설정한다.", "선불 크레딧과 지출 한도를 확인한다."], [("X_USER_ACCESS_TOKEN", "쓰기 권한 사용자 액세스 토큰", 1)], 'python cli.py x --text "설정 테스트"', "요청별 비용이 발생할 수 있다. 현재 미디어 업로드는 HOLD다.", [("Create Posts", "https://docs.x.com/x-api/posts/create-post"), ("가격", "https://docs.x.com/x-api/getting-started/pricing")]),
    ("kakao", "KakaoTalk", "본인에게 메시지 보내기", ["Kakao Developers에 앱과 Redirect URI를 등록한다.", "카카오 로그인과 동의 항목을 구성한다.", "친구 발송은 별도 심사가 필요함을 구분한다."], [("KAKAO_ACCESS_TOKEN", "카카오 로그인 사용자 토큰", 1)], 'python cli.py kakao --text "검토할 초안"', "카카오채널 공개 게시 API가 아니다. 현재는 본인 메시지만 지원한다.", [("카카오톡 메시지", "https://developers.kakao.com/docs/ko/kakaotalk-message/common")]),
    ("naver", "Naver 공유", "사용자 주도 공유 화면", ["별도 개발자 앱이나 토큰 설정은 필요하지 않다.", "공유할 공개 HTTPS URL과 제목을 준비한다.", "공유 화면에서 사용자가 로그인·편집·전송한다."], [], 'python cli.py naver --title "공유 제목" --text "공유 제목" --media-url "https://example.com/article"', "자동 게시가 아니며 사용자의 최종 조작 없이 실행하지 않는다.", [("Naver 공유", "https://developers.naver.com/docs/share/navershare/")]),
    ("naver_cafe", "Naver Cafe", "공식 Cafe 텍스트·링크 글쓰기", ["Naver Developers에 네이버 로그인 앱을 등록한다.", "Cafe API 권한·Redirect URI·사용자 OAuth 동의를 구성한다.", "대상 카페 ID와 게시판 menu ID를 확인한다."], [("NAVER_ACCESS_TOKEN", "네이버 로그인 OAuth 토큰", 1), ("NAVER_CAFE_ID", "카페 숫자 ID", 0), ("NAVER_CAFE_MENU_ID", "게시판 숫자 ID", 0)], 'python cli.py naver_cafe --title "카페 제목" --text "카페 본문"', "multipart 이미지 첨부는 후속 범위다.", [("Cafe 글쓰기", "https://developers.naver.com/docs/login/cafe-api/cafe-api.md")]),
    ("facebook_page", "Facebook Page", "Page 텍스트·링크·원격 미디어", ["Meta 앱과 Facebook Login을 설정한다.", "대상 Page의 관리 역할과 게시 권한을 승인받는다.", "개발 Page에서 Page ID와 Page token의 대상을 확인한다."], [("FACEBOOK_PAGE_ID", "게시 대상 Page ID", 0), ("FACEBOOK_PAGE_ACCESS_TOKEN", "Page access token", 1), ("META_GRAPH_VERSION", "예: v24.0; 선택값", 0)], 'python cli.py facebook_page --text "Page 설정 테스트"', "실제 Page 역할·권한을 개발 Page에서 확인해야 하며 Reels는 HOLD다.", [("Pages API", "https://developers.facebook.com/docs/pages-api/")]),
    ("youtube", "YouTube", "영상 업로드 경계만 정의", ["Google Cloud에서 YouTube Data API v3를 활성화한다.", "OAuth 동의 화면과 클라이언트를 구성한다.", "videos.insert 사용자 동의를 받아 토큰을 준비한다."], [("YOUTUBE_ACCESS_TOKEN", "Google 사용자 OAuth 토큰", 1)], 'python cli.py youtube --title "테스트 영상" --text "설명" --media-type VIDEO --media-url "https://example.com/video.mp4"', "현재 실행은 차단된다. resumable 업로더가 없고 Community 글 API도 확인되지 않았다.", [("videos.insert", "https://developers.google.com/youtube/data/reference/rest/v3/videos/insert")]),
    ("linkedin", "LinkedIn", "텍스트·사전 업로드 자산 URN", ["LinkedIn Developer 앱과 OAuth Redirect URI를 설정한다.", "개인 또는 조직 게시 권한을 준비한다.", "게시 주체의 person 또는 organization URN을 확인한다."], [("LINKEDIN_ACCESS_TOKEN", "사용자 OAuth 토큰", 1), ("LINKEDIN_AUTHOR_URN", "person 또는 organization URN", 0), ("LINKEDIN_VERSION", "예: 202610; 선택값", 0)], 'python cli.py linkedin --text "설정 테스트"', "바이너리 업로드는 HOLD이며 이미 발급된 미디어 URN만 연결한다.", [("Posts API", "https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api")]),
    ("discord", "Discord", "Incoming Webhook 텍스트·원격 링크", ["서버의 대상 채널 설정을 연다.", "연동에서 Incoming Webhook을 만들고 채널을 지정한다.", "Webhook URL을 복사하고 노출되면 재생성한다."], [("DISCORD_WEBHOOK_URL", "ID와 토큰을 포함한 전체 Webhook URL", 1)], 'python cli.py discord --text "설정 테스트"', "Webhook URL 자체가 비밀값이다. 파일 multipart는 HOLD다.", [("Webhook Resource", "https://docs.discord.com/developers/resources/webhook")]),
    ("reddit", "Reddit", "텍스트·링크 제출", ["Reddit 정책에 맞는 앱과 사용자 OAuth를 준비한다.", "대상 subreddit과 게시 유형·규칙을 확인한다.", "자동 반복 게시 전 스팸 정책을 검토한다."], [("REDDIT_ACCESS_TOKEN", "사용자 OAuth 토큰", 1), ("REDDIT_SUBREDDIT", "r/를 제외한 subreddit 이름", 0)], 'python cli.py reddit --title "설정 테스트" --text "본문"', "이미지·영상 업로드와 Devvit 문맥은 HOLD다.", [("submitPost", "https://developers.reddit.com/docs/api/public-api/classes/RedditClient")]),
]


def guide(item: tuple) -> str:
    """Render one standalone guide with site and local settings separated."""
    pid, name, scope, site, values, command, hold, links = item
    rows = "".join(f"<tr><td><code>{escape(k)}</code></td><td>{escape(d)}</td><td>{'비밀값' if s else '식별값'}</td></tr>" for k, d, s in values)
    env = "\n".join(f'$env:{k}="본인이 발급·확인한 값"' for k, _, _ in values)
    env_html = (f"<table><tr><th>환경변수</th><th>가져올 값</th><th>취급</th></tr>{rows}</table><pre><code>{escape(env)}</code></pre>" if values else '<p class="ok">필수 환경변수가 없습니다.</p>')
    official = " · ".join(f'<a href="{escape(url)}">{escape(label)}</a>' for label, url in links)
    steps = "".join(f"<li>{escape(step)}</li>" for step in site)
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(name)} 설정</title><link rel="stylesheet" href="styles.css"></head><body><header><a href="index.html">← 전체 커뮤니티</a><span>{escape(pid)}</span></header><main><section class="hero"><p>COMMUNITY SETUP</p><h1>{escape(name)}</h1><p>{escape(scope)}</p></section><section><h2>1. 커뮤니티 사이트에서 설정할 부분</h2><ol>{steps}</ol><p>공식 문서: {official}</p></section><section><h2>2. 사이트에서 가져올 값과 환경 설정</h2>{env_html}<p class="note"><code>.env.example</code>은 변수명 참고용입니다. 현재 앱은 <code>.env</code>를 자동으로 읽지 않으므로 실제 값은 실행할 PowerShell 세션 또는 비밀 저장소에 설정합니다.</p></section><section><h2>3. 설정 존재 여부 확인</h2><pre><code>python doctor.py --platform {escape(pid)}</code></pre><p>READY는 값 존재만 뜻하며 유효한 토큰·권한·게시 성공을 보증하지 않습니다.</p></section><section><h2>4. 외부 전송 없는 드라이런</h2><pre><code>{escape(command)}</code></pre><p>실제 전송에는 <code>--execute --confirm</code>이 모두 필요합니다.</p></section><section class="hold"><h2>5. 실제 연결 테스트 전 HOLD</h2><p>{escape(hold)}</p><ul><li>토큰을 채팅·HTML·Git·로그에 넣지 않습니다.</li><li>합성 테스트 문구만 사용합니다.</li><li>대상·본문·비용을 사람이 확인한 뒤 실제 전송합니다.</li></ul></section></main><footer>Community Integrations · 실제 비밀값 미포함</footer></body></html>'''


def index() -> str:
    """Render the index linking all platform guides."""
    cards = "".join(f'<a class="card" href="{p[0]}.html"><strong>{escape(p[1])}</strong><span>{escape(p[2])}</span></a>' for p in PLATFORMS)
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>커뮤니티 연동 설정</title><link rel="stylesheet" href="styles.css"></head><body><main><section class="hero"><p>COMMUNITY INTEGRATIONS</p><h1>커뮤니티별 연동 설정</h1><p>사이트 설정과 로컬 환경값을 분리한 13개 안내서입니다.</p></section><section><h2>커뮤니티 선택</h2><div class="grid">{cards}</div></section><section class="note"><h2>공통 순서</h2><ol><li>사이트에서 앱·권한·대상을 설정합니다.</li><li>발급값을 PowerShell 환경변수로 설정합니다.</li><li>doctor로 누락을 확인합니다.</li><li>기본 CLI로 외부 전송 없는 드라이런을 확인합니다.</li><li>실제 전송 직전에 HOLD를 다시 확인합니다.</li></ol></section></main><footer>Community Integrations · 13개 공식 연동 경계</footer></body></html>'''


def main() -> None:
    """Write the shared stylesheet, index, and platform guides."""
    OUTPUT.mkdir(parents=True, exist_ok=True)
    css = """*{box-sizing:border-box}body{margin:0;background:#f4f6fb;color:#172033;font:16px/1.65 system-ui,sans-serif}header,main,footer{max-width:980px;margin:auto;padding:20px}header{display:flex;justify-content:space-between}a{color:#553ee8}main{display:grid;gap:20px}section{background:#fff;border:1px solid #dfe4ef;border-radius:18px;padding:24px}.hero{background:linear-gradient(135deg,#5d43f0,#8b5cf6);color:#fff}.hold{border-color:#f5c76b;background:#fff8e8}.note{background:#eef4ff;padding:12px}.ok{color:#147a52;font-weight:700}h1,h2{line-height:1.25}pre{overflow:auto;background:#141827;color:#eaf0ff;border-radius:12px;padding:16px}code{font-family:Consolas,monospace}table{width:100%;border-collapse:collapse}th,td{text-align:left;border-bottom:1px solid #e3e7ef;padding:10px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.card{display:grid;text-decoration:none;color:inherit;border:1px solid #ddd7ff;border-radius:14px;padding:16px}.card span{color:#667085;font-size:.9rem}footer{text-align:center;color:#667085}@media(max-width:620px){header,main,footer{padding:14px}section{padding:18px}table{font-size:.86rem}}"""
    (OUTPUT / "styles.css").write_text(css, encoding="utf-8")
    (OUTPUT / "index.html").write_text(index(), encoding="utf-8")
    for item in PLATFORMS:
        (OUTPUT / f"{item[0]}.html").write_text(guide(item), encoding="utf-8")


if __name__ == "__main__":
    main()

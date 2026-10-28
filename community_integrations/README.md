# 커뮤니티 자동 게시 통합

공식 API가 허용하는 범위에서 Threads, Instagram, Telegram, TikTok, X, KakaoTalk, Naver Cafe, Facebook Page, YouTube, LinkedIn, Discord, Reddit을 플랫폼별로 구분하는 초보자용 프로젝트입니다. 플랫폼이 지원하는 미디어와 현재 코드가 구현한 미디어를 별도로 표시하며, 브라우저 쿠키·비밀번호·화면 매크로 방식은 사용하지 않습니다.

## 5분 시작

1. Python 3.11 이상을 준비합니다.
2. [`.env.example`](.env.example)을 보고 필요한 값을 **운영체제 환경변수**에 등록합니다. 실제 토큰을 파일에 커밋하지 마세요.
3. 토큰 값을 출력하지 않는 설정 점검을 실행합니다.

```powershell
python doctor.py
python doctor.py --platform telegram
```

`READY`는 환경변수 이름이 채워졌다는 뜻일 뿐 OAuth, 권한, 앱 심사, 실제 게시 성공을 보증하지 않습니다.

미디어 지원표는 다음 명령으로 확인합니다.

```powershell
python capabilities.py
python capabilities.py --platform linkedin
```

4. 먼저 미리보기만 실행합니다.

```powershell
cd <AI_TEST2_ROOT>\community_integrations
$env:TELEGRAM_BOT_TOKEN = "발급받은 값"
$env:TELEGRAM_CHAT_ID = "@채널사용자명"
python cli.py telegram --text "테스트 메시지"
```

5. 출력에 토큰이 없고 대상·본문이 맞는지 사람이 확인한 다음에만 실제 전송합니다.

```powershell
python cli.py telegram --text "테스트 메시지" --execute --confirm
```

`--execute`와 `--confirm` 중 하나라도 빠지면 실제 게시하지 않습니다.

## 지원표 (2026-10-27 확인)

| 플랫폼 | 공식 자동화 범위 | 이 프로젝트 | 주요 HOLD |
|---|---|---|---|
| [Threads](platforms/threads.md) | 글·이미지·영상 게시 | 실행 어댑터 | Meta 앱/권한/토큰, 공개 미디어 URL |
| [Instagram](platforms/instagram.md) | 전문 계정 이미지·영상·Reels·일부 Stories | 실행 어댑터 | 개인 계정 불가, 권한·컨테이너 처리 |
| [Telegram](platforms/telegram.md) | Bot이 권한 있는 채팅/채널에 메시지·미디어 전송 | 실행 어댑터 | Bot 관리자 권한, 대상 chat_id |
| [TikTok](platforms/tiktok.md) | 승인된 Content Posting API로 영상·사진 Direct Post | 실행 어댑터 | `video.publish`, 앱 감사 전 비공개 제한, 검증 도메인, 내부 전용 도구 정책 부적합 가능성 |
| [X](platforms/x.md) | X API v2로 Post 생성 | 실행 어댑터 | OAuth 사용자 토큰, 요청별 과금 |
| [KakaoTalk](platforms/kakao.md) | 본인/동의한 같은 서비스 친구에게 메시지 | 제한 실행 어댑터 | 공개 커뮤니티 게시가 아님, 친구 발송 권한 심사 |
| [Naver](platforms/naver.md) | Cafe 글·이미지 API, Blog 글쓰기 종료, 공유 화면 | Cafe 텍스트·링크 / 공유 수동 | Cafe 이미지 multipart 미구현 |
| [Facebook Page](platforms/facebook_page.md) | 글·링크·이미지·영상·조건부 Reels | 글·링크·원격 이미지·영상 | 공식 문서 429로 라이브 재검증 필요 |
| [YouTube](platforms/youtube.md) | 영상 업로드 | 잘못된 Community 자동화를 차단 | resumable 파일 업로더 미구현 |
| [LinkedIn](platforms/linkedin.md) | 글·이미지·영상·문서·기사 | 글·사전 업로드 미디어 URN | 자산 바이너리 업로드 미구현 |
| [Discord](platforms/discord.md) | 글·임베드·이미지·영상·오디오·파일 | 글·원격 링크·이미지 임베드 | multipart 파일 업로드 미구현 |
| [Reddit](platforms/reddit.md) | 글·링크·이미지·영상/GIF | 글·링크 | 미디어 업로드/Devvit 흐름 미구현 |

## 명령 예시

```powershell
python cli.py threads --text "안녕하세요"
python cli.py instagram --text "새 이미지" --media-type IMAGE --media-url "https://example.com/image.jpg"
python cli.py tiktok --text "영상 설명" --media-type VIDEO --media-url "https://media.example.com/video.mp4"
python cli.py x --text "새 소식"
python cli.py kakao --text "검토할 초안"
python cli.py naver_cafe --title "카페 제목" --text "카페 본문"
python cli.py facebook_page --text "Page 공지"
python cli.py linkedin --text "회사 소식"
python cli.py discord --text "서버 공지"
python cli.py reddit --title "제목" --text "본문"
```

미리보기가 맞으면 끝에 `--execute --confirm`을 붙입니다. `naver` 공유 화면과 `youtube` 미완성 업로드는 의도적으로 실행되지 않습니다.

## 구조

```text
community_integrations/
├─ cli.py                         # 미리보기 우선 CLI
├─ doctor.py                      # 비밀값 없는 설정 점검
├─ capabilities.py                # 플랫폼·미디어 지원표
├─ integration-contract.json      # 다른 로컬 앱이 소비하는 비밀값 없는 계약
├─ community_integrations/
│  └─ publisher.py               # 공통 계약과 13개 플랫폼/서비스 경계
├─ platforms/                    # 초보자용 플랫폼별 설정 가이드
├─ docs/                         # 설계·보안·검증 문서
├─ reports/                      # 공식 근거 기반 조사 보고서
├─ tests/                        # 네트워크 없는 계약 테스트
└─ threads/                      # 기존 Threads 학습 UI/예제(호환 유지)
```

## 검증

```powershell
python -m unittest discover -s tests -v
Push-Location threads
python -m unittest discover -s tests -v
python -m unittest discover -s examples\threads_python\tests -v
Pop-Location
```

전체 오프라인 검증은 아래 한 명령으로 계약 테스트, 보안 검사와 실행기 검사를 순서대로 실행합니다. 실제 커뮤니티 API는 호출하지 않습니다.

```powershell
python verify_offline.py
```

`integration-contract.json`에는 플랫폼 ID·표시명·환경변수 **이름**·기능 범위·설정 문서 경로만 있고 토큰 값은 포함하지 않습니다. 외부 소비자는 이 공개 계약을 독립적으로 검증해 사용할 수 있습니다.

실제 계정 게시 테스트는 외부 게시·토큰·심사·X 비용을 수반하므로 자동 테스트에 포함하지 않습니다. 실행 전 [HOLD 조건](docs/HOLD_CONDITIONS.md)을 확인하세요.

## 문서

- [제품 범위와 완료 기준](docs/SPEC.md)
- [구조와 게시 흐름](docs/ARCHITECTURE.md)
- [보안 경계](docs/SECURITY_BOUNDARY.md)
- [HOLD 조건](docs/HOLD_CONDITIONS.md)
- [검증 절차](docs/VERIFICATION.md)
- [커뮤니티별 HTML 설정 안내](docs/community-setup/index.html)
- [2026-10-27 재검증·남은 작업](docs/REVALIDATION_2026-10-27.md)
- [공식 근거 조사 보고서](reports/커뮤니티 자동 게시 통합.md)
- [글·이미지·영상·음악·파일 기능 매트릭스](reports/커뮤니티 미디어 기능 매트릭스.md)

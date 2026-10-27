# 7개 플랫폼 재검증 결과

> 후속 정정: 같은 날 추가 공식 조사에서 Naver Cafe OAuth 글쓰기 API와 multipart 이미지 예제가 확인됐습니다. 따라서 아래 최초 7개 판정 중 “Naver는 공유 화면만”이라는 문장은 Naver 전체가 아니라 Blog/공유 경로에만 적용됩니다. 최신 종합 상태는 [커뮤니티 미디어 기능 매트릭스](../reports/커뮤니티%20미디어%20기능%20매트릭스.md)를 기준으로 합니다.

확인일: 2026-10-27
판정 범위: 공식 문서 대조, 코드 계약, 네트워크 없는 자동 테스트. 실제 계정 게시와 앱 심사는 포함하지 않음.

## 결론

현재 상태는 **7개 플랫폼 조사·설계·오프라인 구현 완료**이며, **7개 모두 실사용 완료**는 아닙니다. 실행 가능한 어댑터는 6개지만 실제 계정으로 검증되지 않았고, Naver는 사용자 공유 화면만 제공합니다.

| 플랫폼 | 오프라인 구현 | 실사용 전 필수 작업 | 현재 판정 |
|---|---|---|---|
| Threads | 컨테이너 생성→상태 확인→게시 | Meta 앱, 사용자 인증, 권한, 테스트 게시 | HOLD-LIVE |
| Instagram | 이미지/영상 컨테이너→상태 확인→게시 | Professional 계정, 권한, Reels/Stories 실물 검증 | HOLD-LIVE |
| Telegram | 텍스트/사진/영상 Bot 전송 | Bot 관리자 권한, 테스트 채널 1건 전송 | HOLD-LIVE |
| TikTok | creator 조회→Direct Post→상태 확인 | OAuth, `video.publish`, 검증 도메인, 앱 감사 적합성 판단 | HOLD-POLICY/LIVE |
| X | 텍스트/URL Post | OAuth 사용자 토큰, 현재 과금 확인, 1건 전송 | HOLD-COST/LIVE |
| KakaoTalk | 본인에게 기본 템플릿 메시지 | 카카오 로그인·`talk_message` 동의, 1건 전송 | HOLD-LIVE; 공개 게시 아님 |
| Naver | 공식 공유 화면 URL 생성 | 사용자가 로그인·편집·최종 전송 | MANUAL-ONLY |

## 이번 재검증에서 보완한 결함

- TikTok의 HTTP 200 오류 봉투를 creator 조회, 게시 초기화, 상태 조회 단계마다 검사합니다.
- KakaoTalk은 `result_code == 0`일 때만 성공으로 판정합니다.
- 현재 미디어 단독 게시를 지원하지 않는 X, Telegram 텍스트, KakaoTalk에서 공백 본문을 네트워크 전에 차단합니다.
- `python doctor.py`로 토큰 값을 출력하지 않고 환경변수 준비 여부와 제한사항을 확인할 수 있습니다.

## 제품화 전에 남은 구현

1. OAuth 시작·콜백·토큰 갱신·철회 흐름. 현재 코드는 이미 발급된 토큰을 입력받는 게시 실행기입니다.
2. 암호화된 토큰 저장소와 계정별 연결 상태 화면. 현재는 운영체제 환경변수만 사용합니다.
3. 예약 발행 큐, 중복 방지 키, 재시도 정책, 게시 이력·감사 로그.
4. X 미디어 업로드. 원격 URL 가져오기를 추가하면 SSRF·용량 제한까지 함께 설계해야 합니다.
5. Instagram Reels/Stories와 TikTok 영상·사진의 실제 파일 규격 및 비동기 처리 검증.
6. 플랫폼별 개발/심사 계정에서 최소 1건의 비공개 테스트와 실제 반환 ID 대조.

## 정책상 중요한 보정

TikTok 공식 공유 지침은 Direct Post 클라이언트가 창작자의 명시적 동의를 받는 공유 경험이어야 하며, 개인 또는 내부 팀 계정만 관리하는 전용 업로더를 허용 사례로 보지 않습니다. 따라서 이 프로젝트의 목적이 개인/사내 계정 무인 운영이라면 TikTok은 기술 구현과 별개로 공개 배포·감사 단계에서 HOLD입니다.

공식 근거: [TikTok Direct Post](https://developers.tiktok.com/docs/en/content-posting-api-reference-direct-post), [TikTok 공유 지침](https://developers.tiktok.com/docs/en/content-sharing-guidelines), [KakaoTalk 메시지 REST API](https://developers.kakao.com/docs/ko/kakaotalk-message/rest-api), [Telegram Bot API](https://core.telegram.org/bots/api), [Naver 공유하기](https://developers.naver.com/docs/share/navershare/).

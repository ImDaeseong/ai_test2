# Threads 연동

Threads API를 처음 배우거나 다른 서비스에 붙이기 전에 독립적으로 계약을 확인하는 자료입니다. `marketing_command_center`와 연결되어 있지 않습니다.

## 빠른 순서

1. 웹 작성기는 `start.bat`을 더블클릭해 실행합니다. 브라우저가 자동으로 `http://127.0.0.1:8765/publisher.html`을 엽니다.
2. 처음 접한다면 [`ELI5.html`](ELI5.html)로 전체 흐름을 이해합니다.
3. [`docs/01_overview.md`](docs/01_overview.md)에서 지원 범위를 확인합니다.
4. [`docs/02_setup_and_auth.md`](docs/02_setup_and_auth.md)에 따라 Meta 앱과 OAuth를 준비합니다.
5. [`docs/03_publishing.md`](docs/03_publishing.md)에서 게시 흐름을 익힙니다.
6. 구현하거나 통합할 때는 [`DESIGN.html`](DESIGN.html)의 경계와 상태 계약을 따릅니다.
7. 토큰 없이 `python -m unittest discover -s tests -v`와 `python -m unittest discover -s examples/threads_python/tests -v`를 실행합니다.

웹페이지 게시에는 `THREADS_ACCESS_TOKEN` 환경변수와 화면의 계정 연결 확인이 필요합니다. CLI 실제 게시에는 `THREADS_USER_ID`, `THREADS_ACCESS_TOKEN`, `--execute`가 모두 필요합니다. 실제 계정 게시 전에는 [`docs/04_operations.md`](docs/04_operations.md)의 HOLD를 확인하십시오.

웹 화면 오른쪽 위의 `계정 설정`에서 환경변수 설정 여부를 확인하고, `계정 연결 확인`을 누르면 Threads `/me` 응답으로 실제 계정 ID와 사용자명을 검증합니다. 현재 내부 조사 자료에는 OAuth 승인 화면의 정확한 시작 URL이 없으므로 로그인 URL을 추정해 넣지 않았습니다.

처음 설정할 때는 [`ACCOUNT_SETUP.html`](ACCOUNT_SETUP.html)의 단계별 안내를 따르십시오. 현재 웹 연결에는 `THREADS_ACCESS_TOKEN`만 필수이고, App ID·App Secret·Redirect URI는 OAuth 자동 연결을 확장할 때 필요합니다.

## 콘텐츠 지원

| 내용 | 상태 | 방법 |
|---|---|---|
| 글 | 지원 | `TEXT` |
| 링크 | 지원 | `TEXT`의 `link_attachment` 또는 본문 URL |
| 그림 | 지원 | 공개 `image_url`을 사용하는 `IMAGE` |
| 영상 | 지원 | 공개 `video_url`을 사용하는 `VIDEO` |
| 캐러셀 | 지원 | 2–20개 자식 컨테이너와 `CAROUSEL` 부모 |
| 독립 음악/오디오 | 미지원 | 공식 `AUDIO` 유형이 확인되지 않음 |
| 음악이 포함된 영상 | 지원 | 오디오 트랙이 포함된 `VIDEO` |

확인 기준일: 2026-10-23. 세부 미디어 규격은 Meta 공식 문서 접근 제한으로 GAP이며 배포 전에 다시 확인해야 합니다.

# Telegram 설정

1. Telegram에서 `@BotFather`와 대화해 `/newbot`으로 Bot을 만듭니다.
2. Bot을 대상 그룹/채널에 추가합니다. 채널 게시라면 Bot에 게시 관리자 권한을 줍니다.
3. 채널 공개 사용자명(예: `@my_channel`) 또는 chat ID를 확인합니다.
4. `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`를 환경변수로 설정합니다.

```powershell
python cli.py telegram --text "테스트"
python cli.py telegram --text "사진" --media-type IMAGE --media-url "https://example.com/a.jpg"
```

공식 근거: [Telegram Bot API](https://core.telegram.org/bots/api), [Bot 만들기 튜토리얼](https://core.telegram.org/bots/tutorial).

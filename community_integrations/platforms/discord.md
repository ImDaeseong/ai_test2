# Discord 설정

Incoming Webhook은 채널에 텍스트, 임베드, 이미지·영상·오디오·문서 파일을 보낼 수 있습니다. 파일 자체 전송은 `multipart/form-data`가 필요합니다.

```powershell
$env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/.../..."
python cli.py discord --text "공지"
python cli.py discord --text "이미지" --media-type IMAGE --media-url "https://example.com/a.jpg"
```

현재 코드는 텍스트, 이미지 임베드, 영상·오디오·문서의 원격 HTTPS 링크를 지원합니다. 로컬 파일 multipart 업로드는 미구현입니다. Webhook URL은 토큰을 포함한 비밀값이므로 문서·로그·Git에 저장하지 마세요. 예기치 않은 `@everyone` 호출을 막기 위해 멘션 파싱을 비활성화합니다.

공식 근거: [Discord Webhook Resource](https://docs.discord.com/developers/resources/webhook), [파일 첨부 안내](https://support.discord.com/hc/en-us/articles/25444343291031-File-Attachments-FAQ).

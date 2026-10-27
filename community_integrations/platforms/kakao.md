# KakaoTalk 설정

중요: Kakao Developers의 카카오톡 메시지 API는 공개 카카오 커뮤니티/채널 피드에 글을 자동 등록하는 API가 아닙니다. 본인 또는 같은 서비스를 이용하고 동의 조건을 충족한 친구에게 메시지를 보내는 기능입니다.

1. Kakao Developers에서 앱을 등록하고 플랫폼/Redirect URI를 설정합니다.
2. 카카오 로그인을 연결하고 필요한 동의 항목을 구성합니다.
3. 본인에게 보내기는 사용자 토큰을 `KAKAO_ACCESS_TOKEN`에 설정합니다.
4. 친구 발송은 별도 사용 권한 심사와 친구 선택 UI/UUID가 필요하므로 이 초보자 어댑터 범위 밖입니다.

```powershell
python cli.py kakao --text "검토할 초안"
```

이 명령은 `나에게 기본 템플릿으로 메시지 발송`만 준비합니다. 채널 구독자에게 일방적으로 보내려면 알림톡/브랜드 메시지 등 별도 비즈니스 제품과 계약·심사를 검토해야 합니다.

공식 근거: [카카오톡 메시지 이해하기](https://developers.kakao.com/docs/ko/kakaotalk-message/common), [FAQ](https://developers.kakao.com/docs/ko/kakaotalk-message/faq).

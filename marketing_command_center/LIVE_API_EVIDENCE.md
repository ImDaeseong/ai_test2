# 실제 OpenAI API 검증 증거

## 2026-10-22 — 채널별 초안 생성

- 경로: Windows 실행기 → 로컬 HTTP 서버 → `/api/ai/draft` → OpenAI Responses API
- 입력: 개인정보가 없는 가상 서비스·대상·가치·신뢰 근거·행동 요청
- 모델: `gpt-6-luna`
- 결과: `generated`
- 사용량: 입력 282토큰, 출력 102토큰, 총 384토큰
- 출력 검증: 192자, 행동 요청 포함
- 계산 비용: `(282 × $0.10 + 102 × $0.50) / 1,000,000 = $0.0000792`
- 비밀 경계: API 키와 원시 공급자 응답은 파일·로그·화면에 기록하지 않음

가격 근거: <https://developers.openai.com/api/docs/models/gpt-6-luna>

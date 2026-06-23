# Channel Management Guide — youtube_research

## channels.json 구조

```json
{
  "channels": [...],
  "search_queries": [...],
  "ai_filter_keywords": [...]
}
```

---

## 채널 추가 방법

`channels.json > channels` 배열에 항목 추가:

```json
{
  "name": "채널명",
  "handle": "@핸들",
  "url": "https://www.youtube.com/@핸들/videos",
  "tags": ["ai-music"],
  "note": "메모"
}
```

화이트리스트에 등록된 채널은 AI 키워드 유무와 관계없이 항상 수집 결과에 포함됩니다.

---

## 검색 쿼리 추가 방법

`channels.json > search_queries` 배열에 yt-dlp 검색 형식으로 추가:

```json
"search_queries": [
  "ytsearch50:AI music suno 2026",
  "ytsearch50:suno ai kpop"
]
```

숫자(50)는 쿼리당 최대 수집 수입니다.

---

## AI 채널 필터 키워드 관리

`channels.json > ai_filter_keywords` 배열에 단어 추가:

```json
"ai_filter_keywords": ["suno", "udio", "ai", "artificial", "neural", "generated", "synth"]
```

채널명에 이 단어 중 하나라도 포함되면 화이트리스트 등록 없이도 수집 대상이 됩니다.

---

## 현재 등록 채널 (2026-06-19 기준)

| 채널 | 핸들 | 특징 |
|------|------|------|
| Suno Music | @suno | Suno 공식 채널 |
| Studio Publivox | @studiopublivox | AI 음악 바이럴 (1,382만 조회) |
| Ai-Fi Covers | @aificovers | AI 커버 전문 |
| ELEVENZ | @elevenzTV | 다양한 장르 |
| Ethernatunes | @Ethernatunes | 앰비언트·로파이 |
| Serene Video AI | @SereneVideoAI | 릴렉싱 AI 음악 |
| AI Automation Labs | @AIAutomationLabs | Suno 튜토리얼 |
| LLLLITL | @LLLLITL | AI 음악 |
| BodoBeats AI | @BodoBeatsMusic | AI 비트 |
| AI Music Neural | @AI_NeuralMusic | 로파이 AI |
| Dan Dingle | @dandingles | 리뷰·반응 포맷 참조용 |
| AI Controversy | @aicontroversy | 트렌드·업계 동향 |

---

## 제외 채널 예시

| 채널 | 제외 이유 |
|------|----------|
| Rick Beato | 음악 비평가 — AI 키워드 없음 |
| Lofi Girl | 로파이 음악 채널 — AI 생성 아님 |
| Retrovivals | 아티스트 — AI 키워드 없음 |

---

## 참조 도구

| 서비스 | 용도 |
|--------|------|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | YouTube 메타데이터 수집 |
| [Suno](https://suno.com) | AI 음악 생성 (수집 대상 플랫폼) |
| [Udio](https://www.udio.com) | AI 음악 생성 (수집 대상 플랫폼) |

# YouTube AI 음악 채널 리서치

AI 음악 유튜버의 제목·조회수·날짜·태그·썸네일을 수집해  
내 채널 개선에 참조하는 벤치마킹 도구.  
아티스트·로파이·비평가 채널을 자동으로 걸러내고 **순수 AI 음악 유튜버만** 분석한다.

---

## 파일 구조

```
youtube_research/
├── run.bat             <- 더블클릭 실행 (Windows)
├── run.py              <- 원클릭 파이프라인 (수집 + 필터 + 썸네일 + 리포트)
├── collect.py          <- 메타데이터 수집 -> output/raw/ 저장
├── analyze.py          <- raw JSON -> 마크다운 리포트 + URL 목록 생성
├── rank_channels.py    <- raw JSON 기준 채널 조회수 랭킹 출력
├── channels.json       <- 수집 대상 채널 목록 + 검색 쿼리 + AI 필터 키워드
└── output/
    ├── raw/        <- 수집 원본 JSON (collect.py / run.py 저장)
    ├── thumbnails/ <- 조회수 TOP 10 썸네일 (.jpg)
    └── reports/    <- 분석 리포트 (.md) + 순위별 URL 목록 (.txt)
```

---

## 설치

```bash
pip install yt-dlp
```

yt-dlp 경로: `%APPDATA%\Python\Python3*\Scripts\yt-dlp.exe` (버전 무관 자동 탐지)

---

## 실행

`run.bat` 더블클릭 -> 자동으로 아래 3단계 순서 실행:

```
[1/3] 수집   - 검색 쿼리 7개 x 30개 = 최대 210개 영상 메타데이터 수집
             - 중복 제거 (video id 기준)
             - 비AI 채널 필터 (아티스트·로파이 등 제외)
             -> output/raw/search_날짜.json 저장
[2/3] 썸네일 - 조회수 TOP 10 썸네일 JPG 다운로드
             -> output/thumbnails/
[3/3] 리포트 - 마크다운 분석 리포트 + 순위별 URL 파일 생성
             -> output/reports/report_날짜.md
             -> output/reports/urls_날짜.txt   <- 클릭해서 바로 확인용
```

완료까지 약 3~5분 소요.

단계별 개별 실행도 가능:

```bash
python collect.py channel 50   # channels.json 채널 수집 -> raw JSON
python collect.py search  30   # 키워드 검색 -> raw JSON
python collect.py thumb        # 최신 raw JSON 기준 썸네일 다운로드
python analyze.py              # 최신 raw JSON -> 리포트 + URL 목록
python rank_channels.py        # 최신 raw JSON -> 채널 조회수 랭킹
```

---

## 출력 파일

### report_날짜.md

| 섹션 | 내용 |
|------|------|
| 1. 조회수 TOP 20 | 제목·채널·조회수·날짜 (YouTube 링크 포함) |
| 2. 채널별 통계 | 영상 수·평균 조회수·총 조회수 |
| 3. 제목 키워드 TOP 30 | 인기 제목에서 자주 나오는 단어 |
| 4. 월별 업로드 트렌드 | 활성 업로드 시기 파악 |
| 5. 인기 태그 TOP 20 | SEO 태그 전략 참고 |
| 6. 내 채널 개선 인사이트 | 키워드·썸네일·업로드 주기·태그 요약 |

### urls_날짜.txt

조회수 높은 순으로 정렬된 YouTube URL 목록.  
클릭해서 바로 해당 영상을 확인할 수 있다.

```
# YouTube 순위별 URL 목록
# 기준: 조회수 높은 순 | 생성: 2026-06-20 07:00 | 총 42개

  1. [ 9,363,304] Ai-Fi Covers        2023-09-01  Mera Dil Bhi Kitna Pagal Hai...
     https://www.youtube.com/watch?v=_meCewF3Y3g

  2. [ 5,542,999] Studio Publivox     2024-03-15  Deep Purple | Child in Time...
     https://www.youtube.com/watch?v=PU3rXr_lb20
...
```

---

## AI 채널 필터

수집된 영상 중 **AI 음악 유튜버만** 남기고 나머지는 자동 제외한다.

### 통과 기준 (OR 조건)

1. **화이트리스트** - `channels.json > channels`에 등록된 채널 (핸들 일치)
2. **키워드 매칭** - 채널명에 아래 단어 중 하나 이상 포함

```
suno  udio  ai  artificial  neural  generated  synth
```

### 제외 예시

| 채널 | 제외 이유 |
|------|----------|
| Rick Beato | 음악 비평가 - AI 키워드 없음 |
| Lofi Girl | 로파이 음악 채널 - AI 키워드 없음 |
| Retrovivals | 아티스트 - AI 키워드 없음 |
| the bootleg boy | 로파이 채널 - AI 키워드 없음 |

### 키워드 추가 방법

`channels.json > ai_filter_keywords` 배열에 단어 추가:

```json
"ai_filter_keywords": ["suno", "udio", "ai", "artificial", "neural", "generated", "synth"]
```

---

## 채널 목록 (channels.json)

AI 음악 채널 12개 등록 (2026-06-19 기준):

| 채널 | 핸들 | 특징 |
|------|------|------|
| Suno Music | @suno | Suno 공식 채널 |
| Studio Publivox | @studiopublivox | 1,382만 조회 - AI 음악 바이럴 |
| Ai-Fi Covers | @aificovers | AI 커버 전문 |
| ELEVENZ | @elevenzTV | 다양한 장르 |
| Ethernatunes | @Ethernatunes | 앰비언트·로파이 |
| Serene Video AI | @SereneVideoAI | 릴렉싱 AI 음악 |
| AI Automation Labs | @AIAutomationLabs | Suno 튜토리얼 |
| LLLLITL | @LLLLITL | AI 음악 |
| BodoBeats AI | @BodoBeatsMusic | AI 비트 |
| AI Music Neural | @AI_NeuralMusic | 로파이 AI |
| Dan Dingle | @dandingles | 리뷰·반응 (포맷 참조) |
| AI Controversy | @aicontroversy | 트렌드·업계 동향 |

채널 추가 방법 - `channels.json > channels` 배열에 항목 추가:

```json
{
  "name": "채널명",
  "handle": "@핸들",
  "url": "https://www.youtube.com/@핸들/videos",
  "tags": ["ai-music"],
  "note": "메모"
}
```

화이트리스트에 등록된 채널은 AI 키워드 유무와 관계없이 항상 결과에 포함된다.

---

## 검색 쿼리 (channels.json)

`channels.json > search_queries`에 등록된 키워드로 수집:

```
AI music suno 2026
AI generated music udio 2026
AI music lofi chill
suno ai song viral
AI cover kpop
AI music channel suno lofi
AI generated song official
```

쿼리 추가·수정은 `channels.json`의 `search_queries` 배열에서 편집.

---

## 참조 사이트

### AI 음악 생성 도구

| 서비스 | URL | 특징 |
|--------|-----|------|
| Suno | https://suno.com | 텍스트->음악, 가장 대중적 |
| Udio | https://www.udio.com | 고음질 생성 |
| Stable Audio | https://www.stableaudio.com | Stability AI |
| Loudly | https://www.loudly.com | 장르별 생성 |

### yt-dlp

| 자료 | URL |
|------|-----|
| GitHub | https://github.com/yt-dlp/yt-dlp |
| 지원 사이트 목록 | https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md |

---

## 주의사항

- 메타데이터(제목·조회수·날짜·태그) 수집은 공개 정보 - 문제 없음
- 음원 파일(.mp3/.m4a) 다운로드는 이 프로젝트 범위 밖 (저작권)
- 요청 과다 방지를 위해 쿼리 간 1초 딜레이 적용

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-06-20 | `rank_channels.py` 절대경로·JSONL 포맷 제거, 최신 raw JSON 자동 선택으로 재작성 |
| 2026-06-20 | `collect.py` yt-dlp 오류 경고 출력, 수집 함수 내 sleep 통합, mkdir 자동 생성 |
| 2026-06-20 | `run.py` collect·analyze import 리팩토링 (중복 코드 275줄 -> 70줄) |
| 2026-06-20 | `analyze.py` STOPWORDS 보강(ai 등 노이즈 제거), 구두점 스트리핑 수정, 키워드 루프 홀수 버그 수정 |
| 2026-06-20 | `analyze.py` 중복 영상 자동 제거 추가 |
| 2026-06-20 | `urls_날짜.txt` 출력 추가 - 조회수 순위별 URL 별도 파일 저장 |
| 2026-06-20 | AI 채널 필터 추가 - 화이트리스트 + 키워드 2단계 필터로 순수 AI 유튜버만 추출 |
| 2026-06-20 | `rank_channels.py` AI 채널 필터 적용 (analyze.py와 결과 일관성 확보) |
| 2026-06-20 | `collect.py _normalize()` None 값 방어 처리 (yt-dlp uploader_id=None 오류 수정) |
| 2026-06-20 | `channels.json` 검색 쿼리 연도 2024 -> 2026 갱신 |

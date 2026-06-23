# 설계 문서 — youtube_research

> AI 음악 YouTube 채널 메타데이터 수집 + 벤치마킹 리포트 자동 생성
> 외부 API 없음. 의존성: yt-dlp (시스템 설치), pytest (테스트용)

---

## 1. 목적과 범위

AI 음악 유튜버의 공개 메타데이터(제목·조회수·날짜·태그·썸네일 URL)를 수집하고, 내 채널 전략 개선에 참고할 수 있는 마크다운 리포트를 생성한다.

**입력**: `channels.json` (채널 목록 + 검색 쿼리 + AI 필터 키워드)  
**출력**: `output/reports/report_날짜.md` + `output/reports/urls_날짜.txt`

**법적 범위**: 공개 메타데이터만 수집. 음원 파일(.mp3/.m4a) 다운로드는 이 프로젝트 범위 밖.

---

## 2. 아키텍처

```
run.py / run.bat
  └→ collect.py    yt-dlp → 원본 JSON 저장 (output/raw/)
  └→ collect.py    썸네일 다운로드 (output/thumbnails/)
  └→ analyze.py    원본 JSON → 마크다운 리포트 + URL 목록
```

### 파일 역할

| 파일 | 역할 |
|---|---|
| `channels.json` | 수집 대상 채널 목록, 검색 쿼리, AI 필터 키워드 |
| `collect.py` | yt-dlp 실행 래퍼, 중복 제거, AI 채널 필터 적용, 썸네일 다운로드 |
| `analyze.py` | 원본 JSON → 6개 섹션 리포트 + URL 목록 생성 |
| `rank_channels.py` | 채널별 조회수 통계 콘솔 출력 (독립 실행) |
| `run.py` | collect → 썸네일 → analyze 순서로 조율 |

---

## 3. 데이터 흐름

```
channels.json
  ├── channels     → yt-dlp로 각 채널의 최신 영상 수집
  ├── search_queries → yt-dlp search로 키워드 검색 수집
  └── ai_filter_keywords

        ↓ collect.py

AI 채널 필터 (2단계)
  1. 화이트리스트: channels.json의 handle과 일치하면 통과
  2. 키워드: 채널명에 ai_filter_keywords 단어 포함 시 통과
  → 아티스트·로파이·비평가 채널 자동 제외

        ↓

output/raw/search_YYYYMMDD_HHMMSS.json
  [{"id", "title", "channel_name", "channel_handle",
    "views", "date", "tags", "thumbnail_url", "url"}, ...]

중복 제거: video id 기준, 동일 id 재등장 시 첫 번째 유지

        ↓ analyze.py

output/reports/report_YYYYMMDD_HHMMSS.md
output/reports/urls_YYYYMMDD_HHMMSS.txt
output/thumbnails/thumb_1_{채널명}.jpg (TOP 10)
```

---

## 4. channels.json 스키마

```json
{
  "channels": [
    {
      "name": "Suno Music",
      "handle": "@suno",
      "url": "https://www.youtube.com/@suno/videos",
      "tags": ["suno", "ai-music"],
      "note": "Suno 공식 채널"
    }
  ],
  "search_queries": [
    "ytsearch50:AI music suno 2026",
    "ytsearch50:AI generated music udio 2026"
  ],
  "ai_filter_keywords": ["suno", "udio", "ai", "artificial", "neural", "generated", "synth"]
}
```

**search_queries 형식**: `ytsearch{N}:{검색어}` — N은 쿼리당 최대 수집 수.

---

## 5. 리포트 구조 (report_날짜.md)

| 섹션 | 내용 |
|---|---|
| 1. 조회수 TOP 20 | 제목·채널·조회수·날짜 (YouTube 링크) |
| 2. 채널별 통계 | 영상 수·평균 조회수·총 조회수 |
| 3. 제목 키워드 TOP 30 | 인기 제목에서 자주 나오는 단어 (STOPWORDS 제거 후) |
| 4. 월별 업로드 트렌드 | YYYY-MM별 업로드 수 |
| 5. 인기 태그 TOP 20 | SEO 태그 전략 참고 |
| 6. 내 채널 개선 인사이트 | 키워드·썸네일·업로드 주기·태그 요약 |

---

## 6. yt-dlp 통합 방식

```python
import subprocess
cmd = ["yt-dlp", "--dump-json", "--flat-playlist",
       "--playlist-end", str(max_videos), url]
result = subprocess.run(cmd, capture_output=True, text=True)
```

yt-dlp 경로는 `shutil.which("yt-dlp")` 자동 탐지.  
Windows의 경우 `%APPDATA%\Python\Python3*\Scripts\yt-dlp.exe`도 탐색.

**요청 과부하 방지**: 쿼리 간 1초 딜레이 (`time.sleep(1)`) 적용.

---

## 7. 알려진 버그 패턴

| 증상 | 원인 | 해결 |
|---|---|---|
| `yt-dlp not found` | yt-dlp 미설치 또는 PATH 문제 | `pip install yt-dlp` 후 터미널 재시작 |
| 수집 결과 0개 | 검색 쿼리가 결과 없음 또는 네트워크 오류 | `channels.json` 쿼리 단순화 또는 연도 갱신 |
| 채널 필터가 너무 넓음 | `ai_filter_keywords`가 일반 단어 포함 | 키워드 목록 축소 또는 화이트리스트 의존도 높임 |
| 중복 영상 등장 | 채널 수집과 검색 결과가 겹침 | 자동 중복 제거 (video id 기준) — 이미 적용됨 |
| 키워드 노이즈 | 제목에 "AI"가 포함된 비AI 채널 | `ai_filter_keywords`에서 단독 "ai" 제거 후 조합 키워드 사용 |

---

## 8. 테스트 전략

```powershell
python -m pytest tests_unit.py -q   # 37 passed
```

- 모든 테스트는 네트워크 호출 없이 실행 (yt-dlp 없이도 통과)
- 대상: 정규화 함수, 필터 로직, 리포트 생성, STOPWORDS 처리
- 실제 수집 테스트: `python run.py search 5` (소량 수집으로 검증)

---

## 9. 확장 시 주의사항

- **새 채널 추가**: `channels.json > channels`에 항목 추가. handle 형식 주의 (`@핸들`).
- **검색 쿼리 연도 갱신**: 매년 초 `search_queries`의 연도 업데이트 권장.
- **STOPWORDS 관리**: `analyze.py`의 `STOPWORDS` 집합에 노이즈 단어 추가. "ai", "music" 등은 이미 포함됨.
- **음원 다운로드 추가 금지**: 저작권 위반. 메타데이터 전용 범위 유지.

---

*Last Updated: 2026-06-23*

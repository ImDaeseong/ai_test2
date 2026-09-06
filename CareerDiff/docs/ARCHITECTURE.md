# Architecture

## 기술 스택

- Next.js App Router, React, TypeScript
- Zod 스키마 검증
- Vitest, Testing Library, Playwright
- 선택적 OpenAI Responses API Structured Outputs

## 주요 구조

```text
app/src/
├── app/
│   └── api/
│       ├── analyze/
│       ├── jobs/import/
│       └── validation-cases/
├── core/
│   ├── analysis/
│   ├── job-import/
│   ├── llm/
│   ├── schemas/
│   ├── types/
│   └── validation/
└── features/
    ├── job-description-input/
    ├── candidate-profile-input/
    └── analysis-dashboard/
```

## 데이터 흐름

```text
채용공고 URL (잡코리아·사람인·인크루트)
→ POST /api/jobs/import
→ 사이트별 공개 HTML 정리
→ 채용공고 본문 + 충분성(sufficient) 판정

채용공고 + 후보자 프로필
→ POST /api/analyze
→ AnalysisOrchestrator
→ 로컬 분석기 또는 OpenAI provider
→ 스키마가 검증된 분석 JSON
→ 화면 렌더링
→ POST /api/validation-cases
→ data/<UUID>.json
```

## API

### `POST /api/jobs/import`

입력: `{ "url": "..." }` — 잡코리아(`/Recruit/GI_Read/<id>`), 사람인
(`/zf_user/jobs/relay/view?rec_idx=<id>`), 인크루트(`/jobdb_info/jobpost.asp?job=<id>`) 상세 URL.

출력: 출처 URL, 제목, 회사명, 정리된 공고 본문, 수집 시각, 충분성(`sufficient`).
`sufficient=false`면 요약만 수집된 것이므로 UI가 상세 요강 직접 붙여넣기를 안내한다.

### `POST /api/analyze`

입력: `jobDescription`, `candidateProfile`.

출력: 요구사항, 후보자 근거, 매칭, 점수, 이력서 제안, 미니 프로젝트, 연관 기술 가이드, 면접 준비와 메타데이터.

### `POST /api/validation-cases`

입력: UUID, 생성 시각, 두 입력 원문과 분석 결과.

출력: 생성 파일명과 신규 생성 여부.

## 저장

- 후보자 첨부와 검증 목록: 브라우저 `localStorage`
- 검증 케이스: 프로젝트 `data/<UUID>.json`
- 파일 저장은 같은 디렉터리의 임시 파일을 완전히 기록·동기화한 뒤 최종 파일로 연결한다.
- 동일 UUID 재시도는 기존 파일을 유지해 중복 효과를 막는다.

## 보안 경계

- 지원 사이트(잡코리아·사람인·인크루트)의 HTTPS 상세공고 호스트와 경로만 화이트리스트로 허용해
  SSRF 범위를 제한한다. 인크루트 `www` 링크는 `job` 서브도메인으로 재작성해 직접 요청한다(리다이렉트는 error).
- 응답 크기와 요청 시간을 제한한다.
- 원문을 서버 로그에 기록하지 않는다.
- 입력을 신뢰할 수 없는 데이터로 취급하며 프롬프트 명령으로 실행하지 않는다.
- `data` 파일에는 개인정보가 포함될 수 있으므로 외부 공유와 버전 관리 전에 검토한다.
- `next.config.ts`의 `outputFileTracingExcludes`로 프로덕션 빌드 트레이스(`.next/**/*.nft.json`)에서
  `data/`를 명시적으로 제외한다 — `validationCaseFileStore.ts`가 `../data`를 동적 경로로 읽고 쓰기
  때문에 제외 설정이 없으면 개인정보가 담긴 검증 케이스 파일이 빌드 산출물에 포함될 수 있다.
- 로그인, CAPTCHA, 접근통제 우회가 필요하면 구현하지 않고 HOLD한다.

## 분석 모드

`OPENAI_API_KEY`가 없으면 입력 공고와 후보자 프로필을 실제로 분석하는 결정론적 로컬 키워드
분석기(`LocalAnalysisProvider`)를 사용합니다. 키가 있으면 `OpenAiAnalysisProvider`가 Structured
Outputs 스키마로 실제 분석을 수행합니다. RAG와 retrieval은 MVP에서 비활성화합니다.

### 개발 단계 방침: API 대신 Claude Code로 반복

`OPENAI_API_KEY`는 아직 연결하지 않는다. 안정화 이전 단계에서는 유료 API 호출 없이, 실제 채용공고로
`data/<UUID>.json` 검증 케이스를 쌓고 그 결과를 Claude Code(웹 Claude Code 프로젝트 또는 Claude
Code cowork)에서 직접 검토해 `LocalAnalysisProvider`의 스킬 사전과 `relatedTo` 온톨로지를 넓히는
방식으로 반복한다 — 실제로 이 저장소의 최근 커밋들(WPF/CATIA/Linux 등 스킬 추가, 온톨로지 관계
확장)이 이 과정으로 진행되었다. 로컬 분석기가 결정론적이라 같은 입력에 같은 결과가 나오므로
API 비용 없이 회귀 테스트가 가능하다.

`OpenAiAnalysisProvider`(및 `OPENAI_API_KEY` 연결)는 로컬 분석기 커버리지가 안정화 단계에
도달했다고 판단될 때 진행한다. 그 전환 시점에는 `docs/VERIFICATION.md`의 "알려진 후속 작업"에
있는 실제 API 검증(합의된 합성 요청으로 스키마 통과 확인)을 먼저 수행한다.

## 연관 기술 가이드 (경량 온톨로지)

`LocalAnalysisProvider`의 `SKILLS` 배열은 각 스킬에 `relatedTo`(다른 스킬 라벨 목록)를 선택적으로
가질 수 있습니다. 부족한 기술은 전부 `relatedSkillGuidance`로 노출됩니다 — `relatedTo`가 없는
항목도 빈 `relatedSkills`와 함께 "직접 학습이 필요하다"는 안내를 받으며 조용히 누락되지 않습니다.
후보자가 직접 연결된 관련 기술을 이미 보유했으면 그 기술을 출발점으로 언급합니다. 직접 연결에
후보자 경험이 없으면 `findBridgePath`가 `relatedTo` 그래프를 최대 3-hop까지 BFS로 순회해 더 먼
연결(예: LangGraph→LangChain→LLM→OpenAI)까지 찾아 학습 경로로 제시합니다. 관계는 RAG↔Vector
DB/LangChain, Docker↔Kubernetes, Next.js→React, PostgreSQL/MySQL→SQL처럼 잘 알려진 기술적
사실만 수동으로 등록하며(전체 스킬 사전을 다 덮지는 않음), 자격증·강의명은
시간이 지나면 바뀌거나 없어질 수 있어 다루지 않습니다(추가하려면 실제 존재 여부를 별도 검증해야
함). 벡터 검색이나 그래프DB가 아닌 TypeScript 배열 조회 + BFS이므로 RAG/Vector DB MVP 비범위와는
무관합니다.

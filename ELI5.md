# ai_test2 — 쉬운 설명 (ELI5)

## 한마디로

AI 뮤직비디오용 이미지·영상 프롬프트 만들기, 유튜브 채널 조사, 채용 적합도
분석 같은 5개의 독립 도구 모음입니다.

## 비유로 설명하면

여러 부서가 한 사무실을 나눠 쓰는 작은 회사를 생각해보세요. 미술팀
(`ai_anime`, `ai_img_video_aiBoygirl`)은 캐릭터 이미지·영상 프롬프트를 만들고,
편집팀(`ai_img_video_prompt_capcut`)은 그걸 CapCut 편집본으로 조립하고,
리서치팀(`youtube_research`)은 경쟁 채널을 조사하고, 채용팀(`CareerDiff`)은
이력서와 채용공고를 비교합니다. 각 팀은 서로 독립적으로 일하되, 미술팀 →
편집팀으로는 결과물이 이어집니다.

## 왜 필요한가요

Suno 음원 하나로 뮤직비디오를 만들려면 "이미지 프롬프트 → 영상 프롬프트 →
편집 타임라인"까지 여러 단계를 거쳐야 하는데, 이 과정을 자동화해서 사람은
음악과 컨셉에만 집중할 수 있게 해줍니다.

## 안에 뭐가 있나요

- `ai_anime` / `ai_img_video_aiBoygirl`: 곡별 캐릭터·이미지·영상 프롬프트 생성
- `ai_img_video_prompt_capcut`: 음원·가사·영상 클립을 CapCut 편집 타임라인으로 조립
- `youtube_research`: 공개된 유튜브 채널 데이터로 경쟁 채널 벤치마킹
- `music_insight_studio`: 로컬 음원의 BPM·음량·믹싱 상태 분석 (다른 팀과 무관하게 독립 동작)
- `CareerDiff`: 채용공고와 이력서의 적합도 분석 웹서비스

> 참고: 예전엔 6번째 도구로 여러 프롬프트를 실행해주는 `ai_multi_agent`가
> 있었지만, 2026-09-18에 애매한 상태로 판단되어 제거했습니다.

## 확인해보려면

```powershell
python -m pytest tests_unit.py -q       # ai_anime, ai_img_video_prompt_capcut, youtube_research
python -m pytest -q                     # ai_img_video_aiBoygirl
python -m unittest discover -s tests    # music_insight_studio
```
각 프로젝트 폴더에서 실행합니다. CareerDiff는 `npm test`를 씁니다.

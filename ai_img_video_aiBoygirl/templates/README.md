# YouTube MV Prompt Templates

이 폴더는 Suno AI 노래를 유튜브 뮤직비디오로 만들기 위한 공통 프롬프트 템플릿 모음이다.

이미지는 **GPT 이미지**에서 생성하고, 영상은 **Google Flow(Veo)** 또는 **Kling AI**에서 이미지 기반 영상으로 생성한다.

## 공통 기준

- 기준 캐릭터 이미지는 `[REFERENCE_DIR]` 폴더를 사용한다.
- 이미지 프롬프트를 사용할 때는 `[REFERENCE_DIR]` 안의 기준 이미지를 항상 함께 첨부한다.
- 영상 프롬프트를 사용할 때는 `[REFERENCE_DIR]`을 참조해 만든 업로드 이미지의 AI Boy/AI Girl 캐릭터 정체성을 유지한다.
- 곡별 폴더를 만들 때는 기준 이미지 사본을 만들지 않는다.
- 곡별 프롬프트 안의 기준 이미지 경로는 공통 `reference` 폴더를 가리켜야 한다.
- AI Boy/AI Girl 치비 토이 로봇 피규어 정체성을 유지한다 (스크린 페이스, 라운드 헬멧, 치비 바디).
- 캐릭터 의상·소품·색상은 장르별로 다르지만 기본 형태는 고정한다.
- 기본 화면비는 YouTube용 16:9로 유지한다.
- 이미지 프롬프트와 영상 Motion Prompt를 섞지 않는다.

## 고정과 변경

모든 곡은 "같은 AI Boy/AI Girl 캐릭터가 다른 노래를 공연한다"는 기준으로 만든다.

항상 고정:

```text
캐릭터 정체성 (AI Boy/AI Girl 3D 치비 토이 로봇 피규어)
기준 이미지 폴더: [REFERENCE_DIR]
스크린 페이스 디스플레이, 라운드 로봇 헬멧, 치비 바디
보컬, 기타, 베이스, 드럼, 분위기, 전체 무대 역할
16:9 YouTube MV 화면비
```

곡마다 변경:

```text
장르
무드
템포
감정
캐릭터 의상·소품·색상 (장르별 roles 딕셔너리)
조명 강도
카메라 움직임
연주 방식 (보컬 액션 포함)
분위기 연출
영상 편집 리듬
특수효과
```

즉, 캐릭터 형태 일관성은 유지하고 영상 연출은 노래마다 장르에 맞게 바꾼다.

## 자동 장르 프로필 매칭

`genre_profiles.json`에 정의된 프로필을 기반으로 장르, 무드, 조명, 카메라, 역할이 자동 추론된다.
입력 파일의 `genre:` 필드나 가사 키워드만으로 프로필이 결정되므로, 별도 설정 없이 곡을 추가하면 된다.

지원 장르 프로필 (20종):

```text
subway       — 환승역 감성, 인디팝, 기차 분위기
hyper-pop    — 하이퍼팝, 스타카토 타이트 비트
dance-pop    — 댄스팝, future house, 클럽 그루브
rock         — 록/메탈, 하이에너지 라이브
jazz         — 재즈, 스윙, 보사노바, 스무스 재즈
ballad       — 발라드, acoustic guitar, 감성 보컬
pop-rap      — 팝랩, 멜로딕 랩, 힘들/버텨 감성
r&b          — R&B, heartbeat groove, 고백 감정
soul-pop     — 신스팝 소울, 심금 후렴, 합창
lo-fi        — lo-fi, cassette, cozy study texture
neo-soul     — neo-soul, warm groove, intimate vocal
psychedelic  — psychedelic, surreal, dreamlike visuals
folk         — folk, acoustic, intimate storytelling
indie        — 인디, bedroom pop, lo-fi, dreamy
afrobeats    — 아프로비츠, 폴리리듬 그루브
synth-pop    — 80s 신스팝, new wave, 레트로
house        — tropical house, acid house, 클럽 그루브
hip-hop      — boom bap, 힙합, trap
ambient      — ambient, restrained atmosphere, minimal motion
defaults     — 감성 시네마틱 팝 (매칭 안 된 장르용)
```

## 보컬 액션 자동 주입

`03_vocal_image_prompt.md`에는 장르 프로필의 `vocal_action` 필드가 `[CHARACTER_VOCAL_ACTION]` 플레이스홀더를 통해 자동으로 주입된다.
예시:

```text
r&b:       free hand trembling near the heart, eyes on the screen-face display
soul-pop:  free hand raised high reaching upward on peak notes, helmet tilt
ballad:    free hand slowly pressed near the chest, head bowed softly
hip-hop:   forward pointed-index-finger gesture on the bar, gentle head bob
```

## 공통 템플릿 파일

```text
01_master_style_prompt.md   — 전체 세계관 기준 장면
02_style_lock_prompt.md     — 캐릭터 고정 기준
03_vocal_image_prompt.md    — 보컬 클로즈업 (vocal_action 자동 주입)
04_guitar_image_prompt.md   — 기타 연주 장면
05_bass_image_prompt.md     — 베이스 연주 장면
06_drum_image_prompt.md     — 드럼 연주 장면
07_stage_image_prompt.md    — 전체 무대 장면
08_atmosphere_image_prompt.md — 분위기/실루엣 장면
09_video_motion_prompts.md  — 영상 모션 프롬프트
```

## 노래별 입력값

대부분의 값은 `genre_profiles.json`에서 자동 추론된다. 직접 지정하면 자동 추론보다 우선한다.

```text
[SONG_TITLE]        : 곡 제목 (자동 추론 또는 title: 필드)
[GENRE]             : 장르 (genre: 필드 또는 preamble 태그에서 자동 추론)
[MOOD]              : 곡 분위기 (mood_rules 자동 매칭)
[TEMPO]             : 템포 (BPM 자동 감지)
[EMOTION]           : 핵심 감정 (emotion_rules 자동 매칭)
[STAGE_ENERGY]      : 무대 에너지 (장르 프로필 자동 적용)
[LIGHTING_STYLE]    : 조명 스타일 (장르 프로필 자동 적용)
[CAMERA_STYLE]      : 카메라 스타일 (장르 프로필 자동 적용)
[SPECIAL_EFFECTS]   : 특수 연출 (장르 프로필 자동 적용)
[CHARACTER_OUTFIT]  : 장르별 의상 (roles 자동 적용)
[CHARACTER_PROP]    : 장르별 소품 (roles 자동 적용)
[CHARACTER_COLOR]   : 장르별 색상 (roles 자동 적용)
[CHARACTER_REFERENCE]: 기준 이미지 경로 (roles 자동 적용)
[CHARACTER_VOCAL]   : 보컬 역할 설명 (roles 자동 적용)
[CHARACTER_VOCAL_ACTION]: 보컬 동작 (roles 자동 적용)
[CHARACTER_GUITAR]  : 기타 역할 설명 (roles 자동 적용)
[CHARACTER_BASS]    : 베이스 역할 설명 (roles 자동 적용)
[CHARACTER_DRUM]    : 드럼 역할 설명 (roles 자동 적용)
[CHARACTER_CROWD]   : 관중 반응 (roles 자동 적용)
[CHARACTER_STAGE]   : 무대 구성 설명 (roles 자동 적용)
```

## 노래별 폴더

곡마다 전용 폴더를 만든다.

예시:

```text
output/들리잖아/
```

곡별 폴더 안에는 해당 곡에 맞게 채운 프롬프트와 실제 제작 순서 README를 둔다.

```text
output/들리잖아/
  01_master_style_prompt.md
  02_style_lock_prompt.md
  ...
  09_video_motion_prompts.md
  00_prompt_overview.md
  README.md                    ← 역할별 연출 방향 + 섹션별 편집 가이드 포함
```

## 복사 후 필수 검수

기존 곡 폴더를 복사해서 새 곡 폴더를 만들 때는, 이전 곡 관련 정보가 남아 있지 않은지 반드시 확인한다.

검수 기준:

```text
이전 곡 제목이 남아 있는가?
이전 곡 가사, 훅, 키워드가 남아 있는가?
이전 곡 장르, 무드, 감정 설명이 남아 있는가?
이전 곡 전용 장면명이나 편집 설명이 남아 있는가?
[SONG_TITLE] 같은 placeholder가 그대로 남아 있는가?
현재 곡과 맞지 않는 표현이 남아 있는가?
공통 reference 폴더가 존재하는가?
프롬프트 기준 경로가 공통 reference 폴더를 가리키는가?
```

권장 검색:

```text
rg -n "이전곡제목|이전곡핵심가사|이전곡장르|이전곡무드|\[SONG_TITLE\]|\[GENRE\]|\[MOOD\]" "output/새곡폴더"
```

검수 후에는 남은 표현을 단순 치환하지 말고, 현재 곡의 감정과 장면에 맞게 다시 써야 한다.

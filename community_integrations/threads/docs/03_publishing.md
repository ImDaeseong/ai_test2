# 3. 게시 방법

## 공통 순서

1. `POST /{threads-user-id}/threads`로 컨테이너를 만듭니다.
2. `GET /{container-id}?fields=id,status,error_message`로 상태를 확인합니다.
3. `FINISHED`이면 `POST /{threads-user-id}/threads_publish`에 `creation_id`를 전달합니다.
4. 반환된 원격 게시 ID를 저장하고 가능하면 다시 조회합니다.

`IN_PROGRESS`는 대기, `FINISHED`는 게시 준비, `PUBLISHED`는 게시됨, `ERROR`와 `EXPIRED`는 중단 상태입니다. 정확한 폴링 간격은 공식 계약으로 확인되지 않았으므로 호출 제한 응답을 우선합니다.

## 유형별 생성 값

```text
글:    media_type=TEXT, text=...
링크:  media_type=TEXT, text=..., link_attachment=https://...
그림:  media_type=IMAGE, image_url=https://..., alt_text=...
영상:  media_type=VIDEO, video_url=https://..., alt_text=...
```

이미지와 영상 URL은 Meta 서버가 인증 없이 접근할 수 있어야 하며 처리가 끝나기 전에 만료되면 안 됩니다.

캐러셀은 각 자식을 `is_carousel_item=true`로 생성하고, 2–20개의 자식 ID를 `children`에 넣어 부모 `CAROUSEL` 컨테이너를 만든 뒤 부모만 게시합니다.

독립 음원 파일을 위한 `AUDIO` 또는 `audio_url`은 공식 게시 계약에서 확인되지 않았습니다. 음악은 링크 또는 오디오 트랙이 포함된 영상으로 다룹니다.

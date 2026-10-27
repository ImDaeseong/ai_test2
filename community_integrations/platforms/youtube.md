# YouTube 설정

YouTube Data API의 공식 생성 기능은 **영상 업로드**입니다. 제목·설명·태그·공개 범위를 영상과 함께 지정할 수 있습니다. 텍스트·이미지만 올리는 YouTube Community 게시물 생성 엔드포인트는 공개 Data API 참조에서 확인되지 않았습니다.

- 영상: `videos.insert` 및 resumable upload 지원.
- 음악: 오디오 파일 단독 업로드가 아니라 권리 있는 오디오를 영상 컨테이너로 제작해 업로드.
- 이미지: 썸네일/워터마크 API는 있으나 Community 이미지 글 생성과 다름.
- 현재 코드: 잘못된 “Community 자동 게시” 주장을 막는 HOLD 어댑터만 제공. 로컬 영상 파일 resumable uploader는 후속 구현 대상.

공식 근거: [videos.insert](https://developers.google.com/youtube/data/reference/rest/v3/videos/insert), [영상 업로드 가이드](https://developers.google.com/youtube/data/guides/uploading_a_video), [API 전체 참조](https://developers.google.com/youtube/data/reference/rest).

# 검증 절차

## 오프라인 자동 검증

```powershell
cd <AI_TEST2_ROOT>\community_integrations
python -m unittest discover -s tests -v
python doctor.py
python capabilities.py
Push-Location threads
python -m unittest discover -s tests -v
python -m unittest discover -s examples\threads_python\tests -v
Pop-Location
```

통과 기준:

- 모든 플랫폼 요청 형식 테스트 PASS.
- 미리보기에 토큰이 없음.
- `--execute`만으로는 외부 요청이 실행되지 않음.
- Naver 공유와 YouTube 미완성 업로드가 차단되고 Naver Cafe 공식 텍스트 경로가 별도로 존재함.
- 기능 매트릭스의 모든 플랫폼이 어댑터 레지스트리와 일치함.
- 기존 Threads 예제 테스트가 회귀하지 않음.
- 설정 점검 출력에 실제 토큰 값이 없음.

## 실제 계정 최소 검증

플랫폼별 테스트용 비공개/개발 계정에서 한 번만 수행합니다.

1. 미리보기 출력 검토.
2. 플랫폼 콘솔에서 권한·공개 범위·비용 확인.
3. `--execute --confirm`으로 합성 문구 1건 전송.
4. 반환된 ID와 플랫폼 화면의 실제 결과 대조.
5. 테스트 게시물 삭제 여부를 사람이 결정하고 토큰을 회전/철회할 필요가 있는지 확인.

실제 게시를 하지 않은 검증은 `PASS (offline only)`로 기록합니다.

# ai_test2 HOLD Conditions

Stop and ask for human review if any condition below occurs.

## Security HOLD

- A real API key, token, password, private key, cookie, or credential is found in tracked files.
- A requested change would commit private user/company/customer data.
- A requested change would add authenticated YouTube scraping, cookies, or non-public analytics collection.
- `CareerDiff`가 사용자 고지 없이 이력서나 채용공고를 외부 모델로 전송한다.
- 실제 후보자 데이터, OpenAI 키 또는 원문 입력이 로그·fixture·검증 JSON에 노출된다.

## Scope HOLD

- A change would rewrite multiple projects at once without a migration plan.
- A refactor would change CLI commands, output file names, or CapCut draft contract without compatibility tests.
- A project starts importing another project's internal Python modules instead of using documented file contracts.

## Verification HOLD

- The same test or verification item fails three times in a row.
- The same file location needs three or more edit attempts in one verification loop.
- A fix in one project causes regressions in another project's documented pipeline.
- README test counts or claims cannot be reproduced with real commands.

## Product HOLD

- Generated prompts appear to imitate a living artist, real performer, or copyrighted visual identity too closely.
- YouTube research outputs imply private metrics or claims not supported by collected public metadata.
- CapCut export changes risk corrupting a user's existing local draft folder.
- `CareerDiff` 결과가 사람 검토 없이 채용·탈락 또는 지원 여부를 자동 결정하도록 사용된다.

## Human Review Required Before

- Public release of the repository or generated examples
- Deleting or moving large existing `input/` working assets
- Changing the CapCut `draft_content.json` writer
- 공개 배포 전 `CareerDiff`의 개인정보 처리, 외부 전송 안내, 적합도 근거와 편향 위험 검토

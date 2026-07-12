# ai_test2 HOLD Conditions

Stop and ask for human review if any condition below occurs.

## Security HOLD

- A real API key, token, password, private key, cookie, or credential is found in tracked files.
- A requested change would commit private user/company/customer data.
- A requested change would add authenticated YouTube scraping, cookies, or non-public analytics collection.

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

## Human Review Required Before

- Public release of the repository or generated examples
- Deleting or moving large existing `input/` working assets
- Changing API provider behavior in `ai_multi_agent`
- Changing the CapCut `draft_content.json` writer

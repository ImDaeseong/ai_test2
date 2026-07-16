# HOLD Conditions

Stop implementation and ask for human review if any condition is true.

## HOLD Conditions

- The project purpose or one-sentence use case changes materially.
- A requested feature sends audio, lyrics, or private metadata to an external service without explicit opt-in.
- A requested feature requires storing API keys or secrets in the repository.
- A requested feature attempts to clone, impersonate, or market a living artist's voice or exact style.
- A file handling change could overwrite files outside `uploads/` or `outputs/`.
- A dependency requires a large model download or GPU setup and the user has not approved it.
- The same verification item fails after three consecutive attempts.
- The same file location needs three or more edits in one verification loop.

## Human Review Required Before

- Adding external API integrations
- Adding automatic publishing or upload to platforms
- Adding paid model dependencies
- Keeping uploaded files long-term
- Comparing a user song against copyrighted reference audio files

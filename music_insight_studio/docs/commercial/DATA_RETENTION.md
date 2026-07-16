# Data Retention

## Current state

The MVP writes uploads to `uploads/` and reports to `outputs/`. These folders are runtime-only and should be gitignored.

## Commercial policy

### Default behavior

- Uploaded audio is temporary.
- Generated reports are temporary.
- No long-term storage unless the user explicitly saves a project.

### Explicit save behavior

When a user explicitly saves:

- Store metadata in database.
- Store audio/report files in object storage.
- Record owner user ID.
- Record creation time and retention policy.
- Allow delete/export.

### Deletion requirements

Deleting a project must delete:

- uploaded audio,
- generated Markdown reports,
- generated JSON reports,
- generated notation files,
- derived analysis metadata if requested,
- future embeddings or search indexes if added.

### Retention periods

Recommended defaults:

- Anonymous temporary upload: delete within 24 hours.
- Logged-in unsaved analysis: delete within 7 days.
- Saved project: keep until user deletes or account policy expires.

## Verification requirements

- Test cleanup of expired temporary uploads.
- Test delete removes reports and notation exports.
- Test user A cannot access user B report files.

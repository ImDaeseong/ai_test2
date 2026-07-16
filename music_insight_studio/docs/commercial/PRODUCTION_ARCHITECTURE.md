# Production Architecture

## Target architecture

```text
Browser UI
  -> Web app / API gateway
  -> Auth and quota checks
  -> Upload service
  -> Analysis job queue
  -> Audio analysis worker
  -> Scoring/report service
  -> Optional notation export service
  -> Object storage + database
```

## Recommended production stack

- API: FastAPI.
- Worker: Celery/RQ/Dramatiq or a simple queue first.
- Storage: object storage for audio/report files.
- Database: PostgreSQL for users, jobs, reports, metadata, plans.
- Cache/queue: Redis if job processing is introduced.
- Frontend: current local HTML can be replaced by a proper web app later.

## Service boundaries

### Upload service

Owns:

- file validation,
- temporary storage,
- malware/content checks if added,
- size/extension/MIME enforcement,
- object-storage write.

### Analysis job service

Owns:

- job creation,
- status transitions,
- retry rules,
- timeout handling,
- user ownership.

### Analysis worker

Owns:

- audio decoding,
- feature extraction,
- scoring,
- report generation,
- notation export if requested.

### Report service

Owns:

- Markdown/JSON/Korean report access,
- report download links,
- expiry/deletion behavior.

### Notation export service

Owns:

- MusicXML/MIDI/lead-sheet export,
- confidence labels,
- limitation wording.

## Dependency direction

- UI must not directly analyze files.
- API routes must not own scoring rules.
- Workers call `AnalysisService` or a production equivalent.
- Report writers should remain format-focused.
- Notation export should consume `EvaluationReport`/audio features and future pitch-event data.

## Migration from current MVP

1. Keep `AnalysisService` as the domain entry point.
2. Move `app.web.server` to `app.web.local_server` or mark it local-only.
3. Add `app.api` for production API contracts.
4. Add `app.jobs` for background analysis.
5. Add `app.storage` for upload/report retention.
6. Add `app.notation` for score-generation exports.

## Non-goal

Do not replace the current local MVP until the production path has tests. The local MVP is useful as a stable demo and regression surface.

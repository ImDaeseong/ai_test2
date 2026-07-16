# Commercial Design Documents

This directory separates commercial-service design from the current local MVP.

## Purpose

The current Music Insight Studio is a local-first CLI/Web MVP. These documents define what must change before it can become a paid or public web service.

## Documents

- `COMMERCIAL_READINESS.md`: current commercial-readiness decision and blockers.
- `PRODUCTION_ARCHITECTURE.md`: target service architecture for public/commercial deployment.
- `WEB_SECURITY.md`: upload, file handling, API, and abuse-control requirements.
- `DATA_RETENTION.md`: uploaded audio, generated reports, and deletion/export policy.
- `COPYRIGHT_POLICY.md`: copyright, artist-cloning, reference-track, and user-content policy.

## Rule

Do not treat the stdlib `http.server` Web MVP as production infrastructure. It is a local demo surface only.

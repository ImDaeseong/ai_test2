# Commercial Readiness

## Decision

Music Insight Studio is commercially promising, but it is not yet ready to be operated as a public paid service.

Current status:

- Local CLI MVP: ready.
- Local Web MVP: ready for demo/local use.
- Commercial SaaS: not ready without production architecture, upload security, data retention, account/billing, and copyright policy work.

## What can be reused

- `AnalysisService` orchestration boundary.
- Audio analyzer and optional DSP fallback design.
- Deterministic scoring classes.
- Markdown/JSON report writers.
- Korean report UX direction.
- Existing test suite and verification habit.

## Commercial blockers

### 1. Production web runtime

The current `app.web.server` uses stdlib `http.server`. It is acceptable for local MVP, but not for public traffic.

Required before commercial launch:

- FastAPI or equivalent API layer.
- ASGI server behind a reverse proxy.
- Request size limits.
- Auth-aware API routes.
- Background job handoff for audio analysis.

### 2. Upload safety

Required before commercial launch:

- File size limit.
- MIME and content sniffing.
- Extension allowlist.
- Audio decode sandboxing or isolated worker.
- Timeout limits.
- Temporary storage cleanup.
- Abuse/rate limits.

### 3. Data retention

Required before commercial launch:

- Uploads are temporary by default.
- Reports are temporary by default unless explicitly saved.
- User delete/export controls.
- Object storage lifecycle policy.
- Derived-data deletion rules.

### 4. Copyright and ethics

Required before commercial launch:

- User must confirm upload rights.
- No artist voice/style cloning feature.
- Reference-track comparison requires rights and explicit consent.
- No revenue, playlist, or platform-success guarantees.

### 5. Accuracy and liability

Required before commercial launch:

- Clear confidence/uncertainty wording.
- Audio-analysis limitation document.
- Human-review language for mastering/release decisions.
- Evaluation dataset for scoring calibration.

### 6. Monetization infrastructure

Required before commercial launch:

- Account model.
- Plan/quota model.
- Payment provider.
- Refund policy.
- Cost model for analysis runtime and storage.

## Commercial path recommendation

Proceed in this order:

1. Keep the local MVP intact.
2. Add production API/worker architecture docs.
3. Add upload and retention controls.
4. Add score-generation/notation feature as an export module, not inside analyzer logic.
5. Introduce auth and saved projects only after temporary upload flow is safe.
6. Add billing after usage/cost limits are measurable.

## Gate

Commercial-readiness gate: HOLD for public launch, PASS for local portfolio/demo.

## 2026-07-12 Local Hardening Update

Implemented first commercial-direction hardening without replacing the local MVP server:

- Added upload size validation.
- Added extension allowlist plus audio file signature sniffing.
- Added `/healthz` for local/process health checks.
- Added basic response security headers: `X-Content-Type-Options`, `Referrer-Policy`, and `Cache-Control: no-store`.
- Kept `AnalysisService` as the shared orchestration boundary for CLI, local web, and future production API/worker paths.

This improves the local demo and makes the production migration boundary clearer, but it does not remove the public-launch HOLD. A paid/public service still needs FastAPI or equivalent, ASGI deployment, auth, quotas, object storage lifecycle policy, background jobs, malware/decoder isolation, and retention/delete/export controls.
